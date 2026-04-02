import { Router } from 'express';
import { login, telegramAuth, qrAuth, getMe, getPermissions } from '../controllers/authController';
import { authenticate } from '../middleware/auth';

const router = Router();

router.post('/login', login);
router.post('/telegram', telegramAuth);
router.post('/qr', qrAuth);
router.get('/me', authenticate, getMe);
router.get('/permissions', authenticate, getPermissions);

export default router;
