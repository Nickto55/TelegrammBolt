import { Router } from 'express';
import authRoutes from './auth';
import dseRoutes from './dse';
import userRoutes from './users';
import inviteRoutes from './invites';
import messageRoutes from './messages';
import logRoutes from './logs';

const router = Router();

router.use('/auth', authRoutes);
router.use('/dse', dseRoutes);
router.use('/users', userRoutes);
router.use('/invites', inviteRoutes);
router.use('/messages', messageRoutes);
router.use('/logs', logRoutes);

export default router;
