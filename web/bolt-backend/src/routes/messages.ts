import { Router } from 'express';
import {
  getMessages,
  sendMessage,
  markAsRead,
  getUnreadCount,
  getChatRooms
} from '../controllers/messageController';
import { authenticate } from '../middleware/auth';

const router = Router();

router.get('/', authenticate, getMessages);
router.get('/rooms', authenticate, getChatRooms);
router.get('/unread-count', authenticate, getUnreadCount);
router.post('/', authenticate, sendMessage);
router.put('/:id/read', authenticate, markAsRead);

export default router;
