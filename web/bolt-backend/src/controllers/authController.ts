import { Response } from 'express';
import bcrypt from 'bcryptjs';
import { User } from '../models';
import { generateToken } from '../utils/jwt';
import { logAction } from '../utils/logger';
import { AuthRequest } from '../middleware/auth';

export const login = async (req: AuthRequest, res: Response) => {
  try {
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ error: 'Username and password are required' });
    }

    const user = await User.findOne({ 
      where: { username },
      attributes: ['id', 'first_name', 'last_name', 'username', 'email', 'photo_url', 'role', 'auth_type', 'telegram_linked', 'status', 'password']
    });

    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const isValidPassword = await bcrypt.compare(password, user.password || '');
    
    if (!isValidPassword) {
      await logAction('warning', 'Failed login attempt', 'LOGIN_FAILED', user.id, { username }, req.ip, req.headers['user-agent'] as string);
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    if (user.status !== 'active') {
      return res.status(403).json({ error: 'Account is inactive or banned' });
    }

    await user.update({ last_login: new Date() });

    const token = generateToken({ 
      id: user.id, 
      username: user.username, 
      role: user.role 
    });

    await logAction('success', 'User logged in', 'LOGIN', user.id, { username }, req.ip, req.headers['user-agent'] as string);

    res.json({
      success: true,
      token,
      user: {
        id: user.id,
        first_name: user.first_name,
        last_name: user.last_name,
        username: user.username,
        email: user.email,
        photo_url: user.photo_url,
        role: user.role,
        auth_type: user.auth_type,
        telegram_linked: user.telegram_linked
      }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const telegramAuth = async (req: AuthRequest, res: Response) => {
  try {
    const { id, first_name, last_name, username, photo_url } = req.body;

    let user = await User.findOne({ where: { telegram_id: id.toString() } });

    if (!user) {
      user = await User.create({
        first_name: first_name || 'Telegram User',
        last_name: last_name || '',
        username: username || `tg_${id}`,
        telegram_id: id.toString(),
        photo_url,
        role: 'initiator',
        auth_type: 'telegram',
        telegram_linked: true,
        status: 'active'
      });
      
      await logAction('success', 'New Telegram user registered', 'TELEGRAM_REGISTER', user.id, { telegram_id: id }, req.ip, req.headers['user-agent'] as string);
    } else {
      await user.update({ last_login: new Date() });
    }

    const token = generateToken({ 
      id: user.id, 
      username: user.username, 
      role: user.role 
    });

    await logAction('success', 'Telegram user logged in', 'TELEGRAM_LOGIN', user.id, { telegram_id: id }, req.ip, req.headers['user-agent'] as string);

    res.json({
      success: true,
      token,
      user: {
        id: user.id,
        first_name: user.first_name,
        last_name: user.last_name,
        username: user.username,
        photo_url: user.photo_url,
        role: user.role,
        auth_type: user.auth_type,
        telegram_linked: user.telegram_linked
      }
    });
  } catch (error) {
    console.error('Telegram auth error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const qrAuth = async (req: AuthRequest, res: Response) => {
  try {
    const { invite_code } = req.body;

    // For demo purposes, accept any code
    const user = await User.create({
      first_name: 'QR User',
      username: `qr_${Date.now()}`,
      role: 'user',
      auth_type: 'qr',
      telegram_linked: false,
      status: 'active'
    });

    const token = generateToken({ 
      id: user.id, 
      username: user.username, 
      role: user.role 
    });

    await logAction('success', 'QR login', 'QR_LOGIN', user.id, { invite_code }, req.ip, req.headers['user-agent'] as string);

    res.json({
      success: true,
      token,
      user: {
        id: user.id,
        first_name: user.first_name,
        role: user.role,
        auth_type: user.auth_type,
        telegram_linked: user.telegram_linked
      }
    });
  } catch (error) {
    console.error('QR auth error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getMe = async (req: AuthRequest, res: Response) => {
  try {
    const user = await User.findByPk(req.user.id, {
      attributes: ['id', 'first_name', 'last_name', 'username', 'email', 'photo_url', 'role', 'auth_type', 'telegram_linked', 'status', 'last_login']
    });

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json({ user });
  } catch (error) {
    console.error('Get me error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getPermissions = async (req: AuthRequest, res: Response) => {
  try {
    const rolePermissions: Record<string, any> = {
      admin: {
        dashboard: true,
        view_dse: true,
        create_dse: true,
        edit_dse: true,
        delete_dse: true,
        chat: true,
        admin_panel: true,
        manage_users: true,
        view_users: true,
        manage_invites: true,
        terminal: true,
        export_data: true,
        export_pdf: true,
        export_excel: true,
        approve_dse_requests: true,
        view_dashboard_stats: true
      },
      responder: {
        dashboard: true,
        view_dse: true,
        create_dse: true,
        edit_dse: true,
        chat: true,
        view_users: true,
        export_data: true,
        export_excel: true,
        approve_dse_requests: true,
        view_dashboard_stats: true
      },
      initiator: {
        dashboard: true,
        view_dse: true,
        create_dse: true,
        chat: true
      },
      user: {
        dashboard: true,
        view_dse: true,
        chat: true
      }
    };

    res.json({ permissions: rolePermissions[req.user.role] || {} });
  } catch (error) {
    console.error('Get permissions error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};
