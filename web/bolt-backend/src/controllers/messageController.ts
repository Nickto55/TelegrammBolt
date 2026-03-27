import { Response } from 'express';
import { Op } from 'sequelize';
import { Message, User } from '../models';
import { logAction } from '../utils/logger';
import { AuthRequest } from '../middleware/auth';

export const getMessages = async (req: AuthRequest, res: Response) => {
  try {
    const { room_id, user_id, dse_id, page = 1, limit = 50 } = req.query;

    const where: any = {};

    if (room_id) {
      where.room_id = room_id;
    }

    if (user_id) {
      where[Op.or] = [
        { sender_id: req.user.id, receiver_id: user_id },
        { sender_id: user_id, receiver_id: req.user.id }
      ];
    }

    if (dse_id) {
      where.dse_id = dse_id;
    }

    const offset = (Number(page) - 1) * Number(limit);

    const messages = await Message.findAll({
      where,
      include: [
        { model: User, as: 'sender', attributes: ['id', 'first_name', 'last_name', 'photo_url'] },
        { model: User, as: 'receiver', attributes: ['id', 'first_name', 'last_name', 'photo_url'] }
      ],
      order: [['created_at', 'ASC']],
      limit: Number(limit),
      offset
    });

    res.json({ data: messages });
  } catch (error) {
    console.error('Get messages error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const sendMessage = async (req: AuthRequest, res: Response) => {
  try {
    const { content, receiver_id, dse_id, room_id, attachments } = req.body;

    if (!content) {
      return res.status(400).json({ error: 'Content is required' });
    }

    const message = await Message.create({
      content,
      sender_id: req.user.id,
      receiver_id,
      dse_id,
      room_id,
      attachments,
      is_read: false
    });

    const messageWithUser = await Message.findByPk(message.id, {
      include: [
        { model: User, as: 'sender', attributes: ['id', 'first_name', 'last_name', 'photo_url'] },
        { model: User, as: 'receiver', attributes: ['id', 'first_name', 'last_name', 'photo_url'] }
      ]
    });

    res.status(201).json({
      success: true,
      data: messageWithUser
    });
  } catch (error) {
    console.error('Send message error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const markAsRead = async (req: AuthRequest, res: Response) => {
  try {
    const { id } = req.params;

    const message = await Message.findByPk(id);

    if (!message) {
      return res.status(404).json({ error: 'Message not found' });
    }

    await message.update({ is_read: true });

    res.json({ success: true });
  } catch (error) {
    console.error('Mark as read error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getUnreadCount = async (req: AuthRequest, res: Response) => {
  try {
    const count = await Message.count({
      where: {
        receiver_id: req.user.id,
        is_read: false
      }
    });

    res.json({ count });
  } catch (error) {
    console.error('Get unread count error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getChatRooms = async (req: AuthRequest, res: Response) => {
  try {
    // Get unique rooms where user has messages
    const rooms = await Message.findAll({
      where: {
        [Op.or]: [
          { sender_id: req.user.id },
          { receiver_id: req.user.id }
        ]
      },
      attributes: ['room_id'],
      group: ['room_id'],
      raw: true
    });

    res.json({ 
      data: rooms.map((r: any) => r.room_id).filter(Boolean)
    });
  } catch (error) {
    console.error('Get chat rooms error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};
