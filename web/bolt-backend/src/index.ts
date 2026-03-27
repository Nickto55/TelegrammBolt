import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import dotenv from 'dotenv';
import { createServer } from 'http';
import { Server } from 'socket.io';

import { sequelize, syncDatabase } from './models';
import routes from './routes';
import { authenticate } from './middleware/auth';
import { logAction } from './utils/logger';

dotenv.config();

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: process.env.CORS_ORIGIN || '*',
    methods: ['GET', 'POST']
  }
});

const PORT = process.env.PORT || 3001;

// Middleware
app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGIN || '*',
  credentials: true
}));
app.use(morgan('dev'));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Static files
app.use('/uploads', express.static('uploads'));

// API Routes
app.use('/api', routes);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// WebSocket handling
io.use(async (socket, next) => {
  try {
    const token = socket.handshake.auth.token;
    if (!token) {
      return next(new Error('Authentication required'));
    }
    
    const jwt = require('jsonwebtoken');
    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'secret');
    socket.data.user = decoded;
    next();
  } catch (error) {
    next(new Error('Invalid token'));
  }
});

io.on('connection', (socket) => {
  console.log('User connected:', socket.data.user?.username);
  
  const userId = socket.data.user?.id;
  
  // Join personal room
  socket.join(`user:${userId}`);
  
  // Join general chat room
  socket.join('general');
  
  // Handle joining specific rooms
  socket.on('join-room', (roomId: string) => {
    socket.join(roomId);
    console.log(`User ${userId} joined room ${roomId}`);
  });
  
  // Handle leaving rooms
  socket.on('leave-room', (roomId: string) => {
    socket.leave(roomId);
    console.log(`User ${userId} left room ${roomId}`);
  });
  
  // Handle new messages
  socket.on('send-message', async (data) => {
    try {
      const { content, receiver_id, room_id, dse_id } = data;
      
      // Broadcast to room or specific user
      if (room_id) {
        io.to(room_id).emit('new-message', {
          content,
          sender_id: userId,
          room_id,
          dse_id,
          created_at: new Date()
        });
      } else if (receiver_id) {
        io.to(`user:${receiver_id}`).emit('new-message', {
          content,
          sender_id: userId,
          receiver_id,
          dse_id,
          created_at: new Date()
        });
      }
    } catch (error) {
      console.error('Socket message error:', error);
    }
  });
  
  // Handle typing indicator
  socket.on('typing', (data) => {
    const { room_id, receiver_id } = data;
    if (room_id) {
      socket.to(room_id).emit('user-typing', { user_id: userId });
    } else if (receiver_id) {
      socket.to(`user:${receiver_id}`).emit('user-typing', { user_id: userId });
    }
  });
  
  // Handle disconnect
  socket.on('disconnect', () => {
    console.log('User disconnected:', socket.data.user?.username);
  });
});

// Make io accessible to routes
app.set('io', io);

// Error handling
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Not found' });
});

// Start server
const startServer = async () => {
  try {
    // Test database connection
    await sequelize.authenticate();
    console.log('Database connection established successfully.');
    
    // Sync models
    await syncDatabase();
    
    // Create default admin user if not exists
    const { User } = require('./models');
    const bcrypt = require('bcryptjs');
    
    const adminExists = await User.findOne({ where: { username: 'admin' } });
    if (!adminExists) {
      await User.create({
        first_name: 'Administrator',
        username: 'admin',
        password: await bcrypt.hash('admin123', 10),
        role: 'admin',
        auth_type: 'admin',
        status: 'active'
      });
      console.log('Default admin user created (username: admin, password: admin123)');
    }
    
    httpServer.listen(PORT, () => {
      console.log(`Server running on port ${PORT}`);
      console.log(`API available at http://localhost:${PORT}/api`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
};

startServer();

export { io };
