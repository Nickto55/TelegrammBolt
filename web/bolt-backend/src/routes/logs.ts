import { Router } from 'express';
import {
  getLogs,
  getLogStats,
  clearOldLogs
} from '../controllers/logController';
import { authenticate, requireRole } from '../middleware/auth';

const router = Router();

router.get('/', authenticate, requireRole('admin'), getLogs);
router.get('/stats', authenticate, requireRole('admin'), getLogStats);
router.post('/clear', authenticate, requireRole('admin'), clearOldLogs);

export default router;
