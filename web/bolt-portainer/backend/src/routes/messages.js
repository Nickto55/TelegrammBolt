const express = require('express');
const router = express.Router();
const { body, validationResult, query } = require('express-validator');
const auth = require('../middleware/auth');
const db = require('../config/database');

// @route   GET /api/messages
// @desc    Get messages (chat history)
// @access  Private
router.get('/', [
  auth,
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 100 }),
  query('dse_id').optional().isUUID()
], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  const page = parseInt(req.query.page) || 1;
  const limit = parseInt(req.query.limit) || 50;
  const offset = (page - 1) * limit;
  const { dse_id } = req.query;

  try {
    let whereClause = '';
    const params = [];
    let paramIndex = 1;

    if (dse_id) {
      whereClause += `WHERE m.dse_id = $${paramIndex}`;
      params.push(dse_id);
      paramIndex++;
    }

    // Get total count
    const countResult = await db.query(
      `SELECT COUNT(*) FROM messages m ${whereClause}`,
      params
    );
    const total = parseInt(countResult.rows[0].count);

    // Get messages with user info
    const result = await db.query(
      `SELECT m.*, u.username, u.avatar_url, u.full_name 
       FROM messages m 
       LEFT JOIN users u ON m.user_id = u.id 
       ${whereClause}
       ORDER BY m.created_at DESC 
       LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`,
      [...params, limit, offset]
    );

    res.json({
      data: result.rows.reverse(), // Return in chronological order
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit)
      }
    });
  } catch (err) {
    console.error('Get messages error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

// @route   POST /api/messages
// @desc    Send message
// @access  Private
router.post('/', [
  auth,
  body('content').trim().notEmpty().withMessage('Message content is required'),
  body('dse_id').optional().isUUID()
], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  const { content, dse_id, message_type = 'text' } = req.body;

  try {
    const result = await db.query(
      `INSERT INTO messages (user_id, dse_id, content, message_type) 
       VALUES ($1, $2, $3, $4) 
       RETURNING *`,
      [req.user.id, dse_id || null, content, message_type]
    );

    // Get user info for the response
    const userResult = await db.query(
      `SELECT username, avatar_url, full_name FROM users WHERE id = $1`,
      [req.user.id]
    );

    const message = {
      ...result.rows[0],
      ...userResult.rows[0]
    };

    // Emit to WebSocket if available
    if (req.app.get('io')) {
      req.app.get('io').emit('message', message);
    }

    res.status(201).json(message);
  } catch (err) {
    console.error('Send message error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

// @route   DELETE /api/messages/:id
// @desc    Delete message
// @access  Private
router.delete('/:id', auth, async (req, res) => {
  try {
    const existing = await db.query('SELECT * FROM messages WHERE id = $1', [req.params.id]);
    
    if (existing.rows.length === 0) {
      return res.status(404).json({ message: 'Message not found' });
    }

    // Users can delete their own messages, admins can delete any
    if (existing.rows[0].user_id !== req.user.id && req.user.role !== 'admin') {
      return res.status(403).json({ message: 'Insufficient permissions' });
    }

    await db.query('DELETE FROM messages WHERE id = $1', [req.params.id]);

    res.json({ message: 'Message deleted successfully' });
  } catch (err) {
    console.error('Delete message error:', err.message);
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;
