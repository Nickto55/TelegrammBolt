const bcrypt = require('bcryptjs');
const db = require('./database');

async function seedDatabase() {
  console.log('Checking if seeding is needed...');

  try {
    // Check if admin user exists
    const adminCheck = await db.query(
      "SELECT * FROM users WHERE role = 'admin' LIMIT 1"
    );

    if (adminCheck.rows.length > 0) {
      console.log('Admin user already exists, skipping seed.');
      return;
    }

    console.log('Seeding database with default data...');

    // Create default admin user
    const salt = await bcrypt.genSalt(10);
    const adminPassword = await bcrypt.hash('admin123', salt);

    const adminResult = await db.query(
      `INSERT INTO users (username, email, password_hash, full_name, role, is_active) 
       VALUES ($1, $2, $3, $4, $5, $6) 
       RETURNING id`,
      ['admin', 'admin@bolt.local', adminPassword, 'System Administrator', 'admin', true]
    );

    console.log('Created admin user: admin / admin123');

    // Create sample manager
    const managerPassword = await bcrypt.hash('manager123', salt);
    const managerResult = await db.query(
      `INSERT INTO users (username, email, password_hash, full_name, role, is_active) 
       VALUES ($1, $2, $3, $4, $5, $6) 
       RETURNING id`,
      ['manager', 'manager@bolt.local', managerPassword, 'Manager User', 'manager', true]
    );

    console.log('Created manager user: manager / manager123');

    // Create sample operator
    const operatorPassword = await bcrypt.hash('operator123', salt);
    const operatorResult = await db.query(
      `INSERT INTO users (username, email, password_hash, full_name, role, is_active) 
       VALUES ($1, $2, $3, $4, $5, $6) 
       RETURNING id`,
      ['operator', 'operator@bolt.local', operatorPassword, 'Operator User', 'operator', true]
    );

    console.log('Created operator user: operator / operator123');

    // Create sample DSEs
    const dseData = [
      {
        name: 'DSE-001 - Main Office',
        description: 'Primary digital signature equipment at main office',
        location: 'Building A, Floor 3',
        status: 'active',
        latitude: 55.7558,
        longitude: 37.6173
      },
      {
        name: 'DSE-002 - Branch Office',
        description: 'Secondary equipment at branch location',
        location: 'Building B, Floor 1',
        status: 'active',
        latitude: 55.7580,
        longitude: 37.6200
      },
      {
        name: 'DSE-003 - Warehouse',
        description: 'Equipment for warehouse operations',
        location: 'Warehouse Complex, Gate 5',
        status: 'pending',
        latitude: 55.7600,
        longitude: 37.6150
      },
      {
        name: 'DSE-004 - Remote Site',
        description: 'Remote location equipment',
        location: 'Remote Office, Room 101',
        status: 'inactive',
        latitude: 55.7500,
        longitude: 37.6100
      }
    ];

    for (const dse of dseData) {
      await db.query(
        `INSERT INTO dse (name, description, location, status, latitude, longitude, created_by) 
         VALUES ($1, $2, $3, $4, $5, $6, $7)`,
        [dse.name, dse.description, dse.location, dse.status, 
         dse.latitude, dse.longitude, adminResult.rows[0].id]
      );
    }

    console.log(`Created ${dseData.length} sample DSE records`);

    // Create sample messages
    const messages = [
      { user_id: adminResult.rows[0].id, content: 'Welcome to the system!' },
      { user_id: managerResult.rows[0].id, content: 'Thanks! Ready to start working.' },
      { user_id: operatorResult.rows[0].id, content: 'DSE-001 is now online and operational.' }
    ];

    for (const msg of messages) {
      await db.query(
        `INSERT INTO messages (user_id, content) 
         VALUES ($1, $2)`,
        [msg.user_id, msg.content]
      );
    }

    console.log(`Created ${messages.length} sample messages`);

    // Log the seed action
    await db.query(
      `INSERT INTO logs (user_id, action, entity_type, details) 
       VALUES ($1, $2, $3, $4)`,
      [adminResult.rows[0].id, 'seed', 'system', JSON.stringify({ message: 'Database seeded with default data' })]
    );

    console.log('Database seeding completed successfully!');

  } catch (error) {
    console.error('Error seeding database:', error.message);
    throw error;
  }
}

module.exports = { seedDatabase };

// Run if called directly
if (require.main === module) {
  seedDatabase()
    .then(() => process.exit(0))
    .catch((err) => {
      console.error(err);
      process.exit(1);
    });
}
