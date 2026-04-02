const express = require('express');
const router = express.Router();
const { body, validationResult, query } = require('express-validator');
const auth = require('../middleware/auth');
const db = require('../config/database');

// @route   GET /api/dse
// @desc    Get all DSEs with filters
// @access  Private
router.get('/', [
  auth,
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 100 }),
  query('status').optional().isIn(['active', 'inactive', 'pending', 'suspended']),
  query('search').optional().trim()
], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  const page = parseInt(req.query.page) || 1;
  const limit = parseInt(req.query.limit) || 20;
  const offset = (page - 1) * limit;
  const { status, search } = req.query;

  try {
    let whereClause = '';
    const params = [];
    let paramIndex = 1;

    if (status) {
      whereClause += `WHERE status = $${paramIndex}`;
      params.push(status);
      paramIndex++;
    }

    if (search) {
      whereClause += whereClause ? ' AND' : 'WHERE';
      whereClause += ` (name ILIKE $${paramIndex} OR description ILIKE $${paramIndex} OR location ILIKE $${paramIndex})`;
      params.push(`%${search}%`);
      paramIndex++;
    }

    // Get total count
    const countResult = await db.query(
      `SELECT COUNT(*) FROM dse ${whereClause}`,
      params
    );
    const total = parseInt(countResult.rows[0].count);

    // Get DSEs
    const result = await db.query(
      `SELECT d.*, u.username as created_by_username 
       FROM dse d 
       LEFT JOIN users u ON d.created_by = u.id 
       ${whereClause}
       ORDER BY d.created_at DESC 
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
    console.error('Get DSEs error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

// @route   GET /api/dse/:id
// @desc    Get DSE by ID
// @access  Private
router.get('/:id', auth, async (req, res) => {
  try {
    const result = await db.query(
      `SELECT d.*, u.username as created_by_username 
       FROM dse d 
       LEFT JOIN users u ON d.created_by = u.id 
       WHERE d.id = $1`,
      [req.params.id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'DSE not found' });
    }

    res.json(result.rows[0]);
  } catch (err) {
    console.error('Get DSE error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

// @route   POST /api/dse
// @desc    Create new DSE
// @access  Private (Admin/Manager)
router.post('/', [
  auth,
  body('name').trim().notEmpty().withMessage('Name is required'),
  body('status').optional().isIn(['active', 'inactive', 'pending', 'suspended']),
  body('latitude').optional().isFloat({ min: -90, max: 90 }),
  body('longitude').optional().isFloat({ min: -180, max: 180 })
], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  // Check permissions
  if (!['admin', 'manager'].includes(req.user.role)) {
    return res.status(403).json({ message: 'Insufficient permissions' });
  }

  const { name, description, location, status, latitude, longitude, metadata } = req.body;

  try {
    const result = await db.query(
      `INSERT INTO dse (name, description, location, status, latitude, longitude, metadata, created_by) 
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8) 
       RETURNING *`,
      [name, description, location, status || 'pending', latitude, longitude, 
       metadata ? JSON.stringify(metadata) : null, req.user.id]
    );

    // Log the action
    await db.query(
      `INSERT INTO logs (user_id, action, entity_type, entity_id, details) 
       VALUES ($1, $2, $3, $4, $5)`,
      [req.user.id, 'create', 'dse', result.rows[0].id, JSON.stringify({ name })]
    );

    res.status(201).json(result.rows[0]);
  } catch (err) {
    console.error('Create DSE error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

// @route   PUT /api/dse/:id
// @desc    Update DSE
// @access  Private (Admin/Manager)
router.put('/:id', [
  auth,
  body('name').optional().trim().notEmpty(),
  body('status').optional().isIn(['active', 'inactive', 'pending', 'suspended']),
  body('latitude').optional().isFloat({ min: -90, max: 90 }),
  body('longitude').optional().isFloat({ min: -180, max: 180 })
], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  // Check permissions
  if (!['admin', 'manager'].includes(req.user.role)) {
    return res.status(403).json({ message: 'Insufficient permissions' });
  }

  const { name, description, location, status, latitude, longitude, metadata } = req.body;

  try {
    // Check if DSE exists
    const existing = await db.query('SELECT * FROM dse WHERE id = $1', [req.params.id]);
    if (existing.rows.length === 0) {
      return res.status(404).json({ message: 'DSE not found' });
    }

    const result = await db.query(
      `UPDATE dse 
       SET name = COALESCE($1, name), 
           description = COALESCE($2, description), 
           location = COALESCE($3, location), 
           status = COALESCE($4, status), 
           latitude = COALESCE($5, latitude), 
           longitude = COALESCE($6, longitude), 
           metadata = COALESCE($7, metadata),
           updated_at = CURRENT_TIMESTAMP
       WHERE id = $8 
       RETURNING *`,
      [name, description, location, status, latitude, longitude, 
       metadata ? JSON.stringify(metadata) : null, req.params.id]
    );

    // Log the action
    await db.query(
      `INSERT INTO logs (user_id, action, entity_type, entity_id, details) 
       VALUES ($1, $2, $3, $4, $5)`,
      [req.user.id, 'update', 'dse', req.params.id, JSON.stringify({ name })]
    );

    res.json(result.rows[0]);
  } catch (err) {
    console.error('Update DSE error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

// @route   DELETE /api/dse/:id
// @desc    Delete DSE
// @access  Private (Admin only)
router.delete('/:id', auth, async (req, res) => {
  // Check permissions
  if (req.user.role !== 'admin') {
    return res.status(403).json({ message: 'Insufficient permissions' });
  }

  try {
    const existing = await db.query('SELECT * FROM dse WHERE id = $1', [req.params.id]);
    if (existing.rows.length === 0) {
      return res.status(404).json({ message: 'DSE not found' });
    }

    await db.query('DELETE FROM dse WHERE id = $1', [req.params.id]);

    // Log the action
    await db.query(
      `INSERT INTO logs (user_id, action, entity_type, entity_id, details) 
       VALUES ($1, $2, $3, $4, $5)`,
      [req.user.id, 'delete', 'dse', req.params.id, JSON.stringify({ name: existing.rows[0].name })]
    );

    res.json({ message: 'DSE deleted successfully' });
  } catch (err) {
    console.error('Delete DSE error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;
