import { Router } from 'express';
import {
  getAllDSE,
  getDSEById,
  createDSE,
  updateDSE,
  deleteDSE,
  restoreDSE,
  getPendingRequests,
  approveRequest,
  rejectRequest,
  getDashboardStats,
  exportToExcel
} from '../controllers/dseController';
import { authenticate, requirePermission } from '../middleware/auth';

const router = Router();

router.get('/', authenticate, getAllDSE);
router.get('/stats', authenticate, requirePermission('view_dashboard_stats'), getDashboardStats);
router.get('/pending', authenticate, requirePermission('approve_dse_requests'), getPendingRequests);
router.get('/export/excel', authenticate, requirePermission('export_data'), exportToExcel);
router.get('/:id', authenticate, getDSEById);
router.post('/', authenticate, requirePermission('create_dse'), createDSE);
router.put('/:id', authenticate, requirePermission('edit_dse'), updateDSE);
router.delete('/:id', authenticate, requirePermission('delete_dse'), deleteDSE);
router.post('/:id/restore', authenticate, requirePermission('delete_dse'), restoreDSE);
router.post('/:id/approve', authenticate, requirePermission('approve_dse_requests'), approveRequest);
router.post('/:id/reject', authenticate, requirePermission('approve_dse_requests'), rejectRequest);

export default router;
