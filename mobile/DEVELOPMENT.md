# RELEASE NOTES

## Version 1.0.0 (Initial Release)

### Features
- ✅ User authentication (Login & Register)
- ✅ Telegram account linking with QR code
- ✅ DSE (Digital Service Enterprise) records management
- ✅ Real-time messaging/chat interface
- ✅ User profile management
- ✅ Offline support for critical features
- ✅ Multi-language support (Russian, English)

### Supported Platforms
- iOS 12.0+
- Android 5.0+ (API 21+)

### Known Issues
- None at this time

### Next Features (Roadmap)
- Push notifications
- Advanced search filters
- File attachments in messages
- Voice messages
- Video calls integration
- Biometric authentication
- Dark mode
- Widget support

---

## Development Setup

### Prerequisites
- Node.js 16+ with npm/yarn
- Expo CLI
- Physical device or emulator

### Quick Start

1. **Clone and navigate:**
   ```bash
   git clone <repo>
   cd TelegrammBolt/mobile
   npm install
   ```

2. **Configure API:**
   ```bash
   cp .env.example .env
   # Edit .env with your API_BASE_URL
   ```

3. **Run:**
   ```bash
   npm start
   # Press 'i' for iOS or 'a' for Android
   ```

### Project Structure

```
mobile/
├── src/
│   ├── screens/         # App screens
│   ├── navigation/      # Navigation setup
│   ├── services/        # API service
│   ├── store/          # Global state
│   ├── components/     # Reusable components
│   ├── utils/          # Utilities
│   ├── hooks/          # Custom hooks
│   └── config/         # Configuration
├── assets/             # Images, icons
├── App.js             # Entry point
└── app.json           # Expo config
```

### Environment Variables

Create `.env` file:

```env
API_BASE_URL=http://your-api.com:5000
API_TIMEOUT=30000
ENABLE_PUSH_NOTIFICATIONS=false
ENABLE_OFFLINE_MODE=true
SECURE_STORAGE_ENABLED=true
```

### Building for Production

#### iOS
```bash
eas build --platform ios --auto-submit
```

#### Android
```bash
eas build --platform android --auto-submit
```

### Code Style

- Use functional components with hooks
- Follow React naming conventions
- Use absolute imports from src
- Keep components small and reusable

### Testing

Run tests (currently configured for Jest):
```bash
npm test
```

### Debugging

1. **React Native Debugger:**
   ```bash
   npm install -g react-native-debugger
   react-native-debugger
   ```

2. **Console logs in terminal:**
   ```bash
   npm start
   ```

3. **Network inspection:**
   Use Chrome DevTools or React Native Debugger

### Common Issues

**Issue:** "Cannot find module '@react-navigation'"
**Solution:** Run `npm install`

**Issue:** "API connection refused"
**Solution:** Check `.env` API_BASE_URL and server is running

**Issue:** "Camera permission denied"
**Solution:** Grant camera permission in app settings

---

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Commit changes: `git commit -am 'Add feature'`
3. Push branch: `git push origin feature/my-feature`
4. Create Pull Request

### Code Guidelines
- Write clear commit messages
- Test your changes before submitting
- Follow existing code style
- Document complex functions

---

## Support

For issues and questions:
1. Check [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)
2. Check documentation in source files
3. Review existing issues
4. Create new issue with detailed description

---

## License

Part of TelegrammBolt project. See main repository for license details.
