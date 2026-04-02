import { Router } from 'express';
import {
  getAllUsers,
  getUserById,
  createUser,
  updateUser,
  deleteUser,
  toggleUserStatus,
  updateProfile,
  changePassword
} from '../controllers/userController';
import { authenticate, requireRole } from '../middleware/auth';

const router = Router();

router.get('/', authenticate, requireRole('admin', 'responder'), getAllUsers);
router.get('/:id', authenticate, getUserById);
router.post('/', authenticate, requireRole('admin'), createUser);
router.put('/:id', authenticate, requireRole('admin'), updateUser);
router.delete('/:id', authenticate, requireRole('admin'), deleteUser);
router.post('/:id/toggle-status', authenticate, requireRole('admin'), toggleUserStatus);
router.put('/profile/me', authenticate, updateProfile);
router.post('/profile/change-password', authenticate, changePassword);

export default router;
