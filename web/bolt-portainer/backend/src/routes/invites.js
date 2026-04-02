const express = require('express');
const router = express.Router();
const crypto = require('crypto');
const { body, validationResult, query } = require('express-validator');
const auth = require('../middleware/auth');
const db = require('../config/database');

// @route   GET /api/invites
// @desc    Get all invites
// @access  Private (Admin/Manager)
router.get('/', [
  auth,
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 100 }),
  query('status').optional().isIn(['pending', 'used', 'expired'])
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
  const { status } = req.query;

  try {
    let whereClause = '';
    const params = [];
    let paramIndex = 1;

    if (status) {
      whereClause += `WHERE i.status = $${paramIndex}`;
      params.push(status);
      paramIndex++;
    }

    // Get total count
    const countResult = await db.query(
      `SELECT COUNT(*) FROM invites i ${whereClause}`,
      params
    );
    const total = parseInt(countResult.rows[0].count);

    // Get invites with creator info
    const result = await db.query(
      `SELECT i.*, 
              u.username as created_by_username,
              us.username as used_by_username
       FROM invites i 
       LEFT JOIN users u ON i.created_by = u.id 
       LEFT JOIN users us ON i.used_by = us.id 
       ${whereClause}
       ORDER BY i.created_at DESC 
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
    console.error('Get invites error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

// @route   POST /api/invites
// @desc    Create new invite
// @access  Private (Admin/Manager)
router.post('/', [
  auth,
  body('role').isIn(['admin', 'manager', 'operator', 'viewer']).withMessage('Invalid role'),
  body('email').optional().isEmail(),
  body('expires_days').optional().isInt({ min: 1, max: 30 })
], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  // Check permissions
  if (!['admin', 'manager'].includes(req.user.role)) {
    return res.status(403).json({ message: 'Insufficient permissions' });
  }

  const { role, email, expires_days = 7 } = req.body;

  try {
    // Generate unique token
    const token = crypto.randomBytes(32).toString('hex');
    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + expires_days);

    const result = await db.query(
      `INSERT INTO invites (token, role, email, expires_at, created_by) 
       VALUES ($1, $2, $3, $4, $5) 
       RETURNING *`,
      [token, role, email || null, expiresAt, req.user.id]
    );

    // Log the action
    await db.query(
      `INSERT INTO logs (user_id, action, entity_type, entity_id, details) 
       VALUES ($1, $2, $3, $4, $5)`,
      [req.user.id, 'create', 'invite', result.rows[0].id, JSON.stringify({ role, email })]
    );

    res.status(201).json({
      ...result.rows[0],
      invite_url: `${process.env.FRONTEND_URL || 'http://localhost'}/register?token=${token}`
    });
  } catch (err) {
    console.error('Create invite error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

// @route   GET /api/invites/validate/:token
// @desc    Validate invite token
// @access  Public
router.get('/validate/:token', async (req, res) => {
  try {
    const result = await db.query(
      `SELECT * FROM invites WHERE token = $1`,
      [req.params.token]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Invalid invite token' });
    }

    const invite = result.rows[0];

    if (invite.status !== 'pending') {
      return res.status(400).json({ message: `Invite is ${invite.status}` });
    }

    if (new Date(invite.expires_at) < new Date()) {
      // Update status to expired
      await db.query(
        'UPDATE invites SET status = $1 WHERE id = $2',
        ['expired', invite.id]
      );
      return res.status(400).json({ message: 'Invite has expired' });
    }

    res.json({
      valid: true,
      role: invite.role,
      email: invite.email
    });
  } catch (err) {
    console.error('Validate invite error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

// @route   POST /api/invites/use/:token
// @desc    Use invite token to register
// @access  Public
router.post('/use/:token', [
  body('username').trim().isLength({ min: 3 }),
  body('password').isLength({ min: 6 }),
  body('full_name').trim().notEmpty()
], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  const { username, password, full_name } = req.body;

  try {
    // Validate token
    const inviteResult = await db.query(
      `SELECT * FROM invites WHERE token = $1`,
      [req.params.token]
    );

    if (inviteResult.rows.length === 0) {
      return res.status(404).json({ message: 'Invalid invite token' });
    }

    const invite = inviteResult.rows[0];

    if (invite.status !== 'pending') {
      return res.status(400).json({ message: `Invite is ${invite.status}` });
    }

    if (new Date(invite.expires_at) < new Date()) {
      await db.query(
        'UPDATE invites SET status = $1 WHERE id = $2',
        ['expired', invite.id]
      );
      return res.status(400).json({ message: 'Invite has expired' });
    }

    // Check if username exists
    const existingUser = await db.query(
      'SELECT * FROM users WHERE username = $1',
      [username]
    );

    if (existingUser.rows.length > 0) {
      return res.status(400).json({ message: 'Username already exists' });
    }

    // Create user
    const bcrypt = require('bcryptjs');
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);

    const userResult = await db.query(
      `INSERT INTO users (username, email, password_hash, full_name, role) 
       VALUES ($1, $2, $3, $4, $5) 
       RETURNING id, username, email, full_name, role`,
      [username, invite.email, hashedPassword, full_name, invite.role]
    );

    // Mark invite as used
    await db.query(
      'UPDATE invites SET status = $1, used_by = $2, used_at = CURRENT_TIMESTAMP WHERE id = $3',
      ['used', userResult.rows[0].id, invite.id]
    );

    res.status(201).json({
      message: 'Registration successful',
      user: userResult.rows[0]
    });
  } catch (err) {
    console.error('Use invite error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

// @route   DELETE /api/invites/:id
// @desc    Delete invite
// @access  Private (Admin only)
router.delete('/:id', auth, async (req, res) => {
  // Check permissions
  if (req.user.role !== 'admin') {
    return res.status(403).json({ message: 'Insufficient permissions' });
  }

  try {
    const existing = await db.query('SELECT * FROM invites WHERE id = $1', [req.params.id]);
    if (existing.rows.length === 0) {
      return res.status(404).json({ message: 'Invite not found' });
    }

    await db.query('DELETE FROM invites WHERE id = $1', [req.params.id]);

    res.json({ message: 'Invite deleted successfully' });
  } catch (err) {
    console.error('Delete invite error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;
