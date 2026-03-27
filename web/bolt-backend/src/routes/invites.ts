import { Router } from 'express';
import {
  getAllInvites,
  createInvite,
  useInvite,
  deleteInvite
} from '../controllers/inviteController';
import { authenticate, requireRole } from '../middleware/auth';

const router = Router();

router.get('/', authenticate, requireRole('admin'), getAllInvites);
router.post('/', authenticate, requireRole('admin'), createInvite);
router.post('/use', authenticate, useInvite);
router.delete('/:id', authenticate, requireRole('admin'), deleteInvite);

export default router;
