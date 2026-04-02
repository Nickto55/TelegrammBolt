const express = require('express');
const router = express.Router();
const { query, validationResult } = require('express-validator');
const auth = require('../middleware/auth');
const db = require('../config/database');

// @route   GET /api/logs
// @desc    Get system logs
// @access  Private (Admin/Manager)
router.get('/', [
  auth,
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 100 }),
  query('action').optional().trim(),
  query('entity_type').optional().trim(),
  query('user_id').optional().isUUID()
], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  // Check permissions
  if (!['admin', 'manager'].includes(req.user.role)) {
    return res.status(403).json({ message: 'Insufficient permissions' });
  }

  const page = parseInt(req.query.page) || 1;
  const limit = parseInt(req.query.limit) || 50;
  const offset = (page - 1) * limit;
  const { action, entity_type, user_id } = req.query;

  try {
    let whereClause = '';
    const params = [];
    let paramIndex = 1;

    if (action) {
      whereClause += `WHERE l.action = $${paramIndex}`;
      params.push(action);
      paramIndex++;
    }

    if (entity_type) {
      whereClause += whereClause ? ' AND' : 'WHERE';
      whereClause += ` l.entity_type = $${paramIndex}`;
      params.push(entity_type);
      paramIndex++;
    }

    if (user_id) {
      whereClause += whereClause ? ' AND' : 'WHERE';
      whereClause += ` l.user_id = $${paramIndex}`;
      params.push(user_id);
      paramIndex++;
    }

    // Get total count
    const countResult = await db.query(
      `SELECT COUNT(*) FROM logs l ${whereClause}`,
      params
    );
    const total = parseInt(countResult.rows[0].count);

    // Get logs with user info
    const result = await db.query(
      `SELECT l.*, u.username, u.full_name 
       FROM logs l 
       LEFT JOIN users u ON l.user_id = u.id 
       ${whereClause}
       ORDER BY l.created_at DESC 
       LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`,
      [...params, limit, offset]
    );

    res.json({
      data: result.rows,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit)
      }
    });
  } catch (err) {
    console.error('Get logs error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

// @route   GET /api/logs/stats
// @desc    Get log statistics
// @access  Private (Admin only)
router.get('/stats', auth, async (req, res) => {
  // Check permissions
  if (req.user.role !== 'admin') {
    return res.status(403).json({ message: 'Insufficient permissions' });
  }

  try {
    // Get action counts
    const actionStats = await db.query(
      `SELECT action, COUNT(*) as count 
       FROM logs 
       GROUP BY action 
       ORDER BY count DESC`
    );

    // Get entity type counts
    const entityStats = await db.query(
      `SELECT entity_type, COUNT(*) as count 
       FROM logs 
       GROUP BY entity_type 
       ORDER BY count DESC`
    );

    // Get daily activity (last 30 days)
    const dailyStats = await db.query(
      `SELECT DATE(created_at) as date, COUNT(*) as count 
       FROM logs 
       WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
       GROUP BY DATE(created_at) 
       ORDER BY date DESC`
    );

    // Get most active users
    const userStats = await db.query(
      `SELECT u.username, u.full_name, COUNT(l.id) as action_count 
       FROM logs l 
       JOIN users u ON l.user_id = u.id 
       WHERE l.created_at >= CURRENT_DATE - INTERVAL '30 days'
       GROUP BY u.id, u.username, u.full_name 
       ORDER BY action_count DESC 
       LIMIT 10`
    );

    res.json({
      actions: actionStats.rows,
      entities: entityStats.rows,
      daily: dailyStats.rows,
      topUsers: userStats.rows
    });
  } catch (err) {
    console.error('Get log stats error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

// @route   DELETE /api/logs
// @desc    Clear old logs (admin only)
// @access  Private (Admin)
router.delete('/', [
  auth,
  query('days').optional().isInt({ min: 1 })
], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  // Check permissions
  if (req.user.role !== 'admin') {
    return res.status(403).json({ message: 'Insufficient permissions' });
  }

  const days = parseInt(req.query.days) || 90;

  try {
    const result = await db.query(
      `DELETE FROM logs 
       WHERE created_at < CURRENT_DATE - INTERVAL '${days} days'
       RETURNING COUNT(*) as deleted_count`
    );

    // Log the action
    await db.query(
      `INSERT INTO logs (user_id, action, entity_type, details) 
       VALUES ($1, $2, $3, $4)`,
      [req.user.id, 'clear', 'logs', JSON.stringify({ days, deleted: result.rows[0].deleted_count })]
    );

    res.json({ 
      message: 'Old logs cleared successfully',
      deleted_count: result.rows[0].deleted_count
    });
  } catch (err) {
    console.error('Clear logs error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;
