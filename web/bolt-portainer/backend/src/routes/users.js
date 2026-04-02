const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const { body, validationResult, query } = require('express-validator');
const auth = require('../middleware/auth');
const db = require('../config/database');

// @route   GET /api/users
// @desc    Get all users
// @access  Private (Admin/Manager)
router.get('/', [
  auth,
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 100 }),
  query('role').optional().isIn(['admin', 'manager', 'operator', 'viewer']),
  query('search').optional().trim()
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
  const limit = parseInt(req.query.limit) || 20;
  const offset = (page - 1) * limit;
  const { role, search } = req.query;

  try {
    let whereClause = '';
    const params = [];
    let paramIndex = 1;

    if (role) {
      whereClause += `WHERE role = $${paramIndex}`;
      params.push(role);
      paramIndex++;
    }

    if (search) {
      whereClause += whereClause ? ' AND' : 'WHERE';
      whereClause += ` (username ILIKE $${paramIndex} OR email ILIKE $${paramIndex} OR full_name ILIKE $${paramIndex})`;
      params.push(`%${search}%`);
      paramIndex++;
    }

    // Get total count
    const countResult = await db.query(
      `SELECT COUNT(*) FROM users ${whereClause}`,
      params
    );
    const total = parseInt(countResult.rows[0].count);

    // Get users (exclude password_hash)
    const result = await db.query(
      `SELECT id, username, email, full_name, role, avatar_url, 
              created_at, last_login, is_active 
       FROM users 
       ${whereClause}
       ORDER BY created_at DESC 
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
    console.error('Get users error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

// @route   GET /api/users/:id
// @desc    Get user by ID
// @access  Private
router.get('/:id', auth, async (req, res) => {
  try {
    // Users can view their own profile, admins/managers can view any
    if (req.user.id !== req.params.id && !['admin', 'manager'].includes(req.user.role)) {
      return res.status(403).json({ message: 'Insufficient permissions' });
    }

    const result = await db.query(
      `SELECT id, username, email, full_name, role, avatar_url, 
              created_at, last_login, is_active 
       FROM users WHERE id = $1`,
      [req.params.id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'User not found' });
    }

    res.json(result.rows[0]);
  } catch (err) {
    console.error('Get user error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

// @route   POST /api/users
// @desc    Create new user (admin only)
// @access  Private (Admin)
router.post('/', [
  auth,
  body('username').trim().isLength({ min: 3 }).withMessage('Username must be at least 3 characters'),
  body('email').isEmail().withMessage('Valid email is required'),
  body('password').isLength({ min: 6 }).withMessage('Password must be at least 6 characters'),
  body('full_name').trim().notEmpty().withMessage('Full name is required'),
  body('role').isIn(['admin', 'manager', 'operator', 'viewer']).withMessage('Invalid role')
], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  // Check permissions
  if (req.user.role !== 'admin') {
    return res.status(403).json({ message: 'Insufficient permissions' });
  }

  const { username, email, password, full_name, role } = req.body;

  try {
    // Check if username exists
    const existingUser = await db.query(
      'SELECT * FROM users WHERE username = $1 OR email = $2',
      [username, email]
    );

    if (existingUser.rows.length > 0) {
      return res.status(400).json({ message: 'Username or email already exists' });
    }

    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);

    const result = await db.query(
      `INSERT INTO users (username, email, password_hash, full_name, role) 
       VALUES ($1, $2, $3, $4, $5) 
       RETURNING id, username, email, full_name, role, created_at`,
      [username, email, hashedPassword, full_name, role]
    );

    // Log the action
    await db.query(
      `INSERT INTO logs (user_id, action, entity_type, entity_id, details) 
       VALUES ($1, $2, $3, $4, $5)`,
      [req.user.id, 'create', 'user', result.rows[0].id, JSON.stringify({ username })]
    );

    res.status(201).json(result.rows[0]);
  } catch (err) {
    console.error('Create user error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

// @route   PUT /api/users/:id
// @desc    Update user
// @access  Private
router.put('/:id', [
  auth,
  body('email').optional().isEmail(),
  body('role').optional().isIn(['admin', 'manager', 'operator', 'viewer'])
], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  const { email, full_name, role, is_active, avatar_url } = req.body;

  try {
    // Users can update their own profile (except role)
    // Admins can update any user including role
    if (req.user.id !== req.params.id && req.user.role !== 'admin') {
      return res.status(403).json({ message: 'Insufficient permissions' });
    }

    // Only admins can change role
    if (role && req.user.role !== 'admin') {
      return res.status(403).json({ message: 'Only admins can change role' });
    }

    const existing = await db.query('SELECT * FROM users WHERE id = $1', [req.params.id]);
    if (existing.rows.length === 0) {
      return res.status(404).json({ message: 'User not found' });
    }

    const result = await db.query(
      `UPDATE users 
       SET email = COALESCE($1, email), 
           full_name = COALESCE($2, full_name), 
           role = COALESCE($3, role), 
           is_active = COALESCE($4, is_active),
           avatar_url = COALESCE($5, avatar_url),
           updated_at = CURRENT_TIMESTAMP
       WHERE id = $6 
       RETURNING id, username, email, full_name, role, avatar_url, is_active, created_at`,
      [email, full_name, role, is_active, avatar_url, req.params.id]
    );

    // Log the action
    await db.query(
      `INSERT INTO logs (user_id, action, entity_type, entity_id, details) 
       VALUES ($1, $2, $3, $4, $5)`,
      [req.user.id, 'update', 'user', req.params.id, JSON.stringify({ email, full_name, role })]
    );

    res.json(result.rows[0]);
  } catch (err) {
    console.error('Update user error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

// @route   DELETE /api/users/:id
// @desc    Delete user
// @access  Private (Admin only)
router.delete('/:id', auth, async (req, res) => {
  // Check permissions
  if (req.user.role !== 'admin') {
    return res.status(403).json({ message: 'Insufficient permissions' });
  }

  // Prevent self-deletion
  if (req.user.id === req.params.id) {
    return res.status(400).json({ message: 'Cannot delete yourself' });
  }

  try {
    const existing = await db.query('SELECT * FROM users WHERE id = $1', [req.params.id]);
    if (existing.rows.length === 0) {
      return res.status(404).json({ message: 'User not found' });
    }

    await db.query('DELETE FROM users WHERE id = $1', [req.params.id]);

    // Log the action
    await db.query(
      `INSERT INTO logs (user_id, action, entity_type, entity_id, details) 
       VALUES ($1, $2, $3, $4, $5)`,
      [req.user.id, 'delete', 'user', req.params.id, JSON.stringify({ username: existing.rows[0].username })]
    );

    res.json({ message: 'User deleted successfully' });
  } catch (err) {
    console.error('Delete user error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;
