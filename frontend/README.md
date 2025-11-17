# AutoJobApplier - Next.js Frontend

Modern, responsive web interface for AutoJobApplier built with Next.js 14, React, TypeScript, and shadcn/ui.

## Features

- ⚡ **Next.js 14** with App Router
- 🎨 **shadcn/ui** - Beautiful, accessible components
- 🌓 **Dark Mode** - Full dark mode support with theme toggle
- 📊 **Real-time Updates** - WebSocket integration for live updates
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🎯 **TypeScript** - Full type safety
- 🎨 **Tailwind CSS** - Utility-first CSS framework

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend server running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

The application will be available at `http://localhost:3000`

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout with theme provider
│   ├── page.tsx            # Main dashboard page
│   └── globals.css         # Global styles with CSS variables
├── components/
│   ├── ui/                 # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── label.tsx
│   │   ├── badge.tsx
│   │   ├── progress.tsx
│   │   └── switch.tsx
│   ├── theme-provider.tsx  # Theme context provider
│   └── theme-toggle.tsx    # Dark mode toggle button
├── lib/
│   └── utils.ts            # Utility functions (cn, etc.)
├── public/                 # Static assets
├── next.config.js          # Next.js configuration
├── tailwind.config.ts      # Tailwind CSS configuration
├── tsconfig.json           # TypeScript configuration
├── components.json         # shadcn/ui configuration
└── package.json            # Dependencies
```

## Pages & Features

### Dashboard
- Real-time statistics cards
  - Total applications
  - Today's applications
  - Success rate
  - Average match score
- Action buttons
  - Search jobs
  - Start applying
  - Stop process
  - Export data
- Live activity feed with WebSocket updates

### Job Search
- Search form with parameters
  - Job titles (comma-separated)
  - Locations (comma-separated)
  - Include keywords (optional)
  - Exclude keywords (optional)
- Real-time search results

### Applications
- List of all submitted applications
- Filter and sort options
- Application details
  - Job title, company, location
  - Match score
  - Application status
  - Date applied

### Configuration
- Application settings
  - Max applications per day
  - Auto-submit toggle
  - Headless mode toggle
- Personal information
  - Name, email, phone
- Resume upload

## Theme System

The application uses CSS variables for theming, allowing easy customization and dark mode support.

### Light Mode Variables
```css
--background: 0 0% 100%;
--foreground: 0 0% 3.9%;
--primary: 0 0% 9%;
--secondary: 0 0% 96.1%;
...
```

### Dark Mode Variables
```css
--background: 0 0% 3.9%;
--foreground: 0 0% 98%;
--primary: 0 0% 98%;
--secondary: 0 0% 14.9%;
...
```

Toggle between themes using the theme toggle button in the sidebar.

## API Integration

The frontend communicates with the FastAPI backend through:

### REST API Endpoints
- `GET /api/config` - Get configuration
- `POST /api/config` - Update configuration
- `GET /api/statistics` - Get application statistics
- `GET /api/applications` - List applications
- `POST /api/search` - Start job search
- `POST /api/apply` - Start application process
- `POST /api/stop` - Stop current process
- `GET /api/export` - Export data to CSV

### WebSocket Connection
- `WS /ws` - Real-time updates for job searches and applications

## Development

### Adding New Components

Use shadcn/ui CLI to add new components:

```bash
npx shadcn-ui@latest add [component-name]
```

For example:
```bash
npx shadcn-ui@latest add table
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
```

### Customizing Theme

Edit `app/globals.css` to modify CSS variables:

```css
:root {
  --primary: 221.2 83.2% 53.3%;  /* Change primary color */
  --radius: 0.75rem;               /* Change border radius */
}
```

### Adding New Pages

Create new route files in the `app` directory:

```
app/
├── page.tsx              # Home page (/)
├── about/
│   └── page.tsx          # About page (/about)
└── settings/
    └── page.tsx          # Settings page (/settings)
```

## Production Deployment

### Build for Production

```bash
npm run build
```

### Deploy Options

#### Vercel (Recommended)
```bash
npm install -g vercel
vercel
```

#### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

#### Static Export (if no dynamic features)
```bash
# Add to next.config.js
output: 'export'

# Build
npm run build
```

## Environment Variables

Create `.env.local` for environment-specific settings:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Troubleshooting

### Build Errors

**Issue**: Module not found errors
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
```

**Issue**: TypeScript errors
```bash
# Regenerate types
npm run build
```

### Runtime Errors

**Issue**: WebSocket connection failed
- Ensure backend is running on port 8000
- Check CORS configuration in backend

**Issue**: Theme not persisting
- Clear browser cache
- Check localStorage permissions

### Performance

**Issue**: Slow page loads
- Use Next.js Image component for images
- Implement code splitting
- Enable static generation where possible

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - See main project README for details

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [shadcn/ui Documentation](https://ui.shadcn.com)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [React Documentation](https://react.dev)
- [TypeScript Documentation](https://www.typescriptlang.org/docs)

---

Built with ❤️ using Next.js and shadcn/ui
