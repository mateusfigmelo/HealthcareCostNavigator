# Healthcare Cost Navigator Frontend

A modern React application built with TypeScript and TailwindCSS that provides a user-friendly interface for the Healthcare Cost Navigator API.

## Features

- **Provider Search**: Search hospitals by DRG code, location, and radius
- **Text Search**: Search hospitals by procedure description or hospital name
- **AI Assistant**: Natural language interface for healthcare queries
- **Health Check**: Monitor API status
- **Responsive Design**: Works on desktop and mobile devices
- **Type Safety**: Full TypeScript support with strict type checking
- **Modern Styling**: Beautiful UI with TailwindCSS

## Tech Stack

- **React 18** with TypeScript
- **TailwindCSS** for styling
- **Axios** for API communication
- **Docker** for containerization

## Quick Start

### Using Docker Compose (Recommended)

1. **Start all services:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Local Development

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm start
   ```

3. **Build for production:**
   ```bash
   npm run build
   ```

## TypeScript Features

- **Strict Type Checking**: Full type safety for all components and API calls
- **Interface Definitions**: Well-defined types for API responses and form data
- **Type Guards**: Runtime type checking for better error handling
- **Generic Components**: Reusable components with type parameters

## TailwindCSS Features

- **Custom Design System**: Extended color palette and typography
- **Responsive Design**: Mobile-first approach with breakpoint utilities
- **Component Classes**: Custom utility classes for common patterns
- **Animations**: Smooth transitions and hover effects
- **Dark Mode Ready**: Built-in support for dark mode (future enhancement)

## API Integration

The frontend communicates with the backend API running on port 8000. The proxy is configured in `package.json` to forward requests to the backend.

## Available Scripts

- `npm start`: Start the development server
- `npm run build`: Build the app for production
- `npm test`: Run tests
- `npm run eject`: Eject from Create React App

## Environment Variables

- `REACT_APP_API_URL`: Backend API URL (default: http://localhost:8000)

## Project Structure

```
src/
├── types.ts          # TypeScript type definitions
├── App.tsx           # Main application component
├── index.tsx         # Application entry point
└── index.css         # TailwindCSS imports and custom styles
```

## Type Definitions

The application includes comprehensive TypeScript definitions for:

- **Hospital**: Hospital data structure
- **AIResponse**: AI assistant response format
- **HealthStatus**: API health check response
- **ProviderSearchForm**: Provider search form data
- **TextSearchForm**: Text search form data
- **TabType**: Available application tabs

## Styling Approach

- **Utility-First**: TailwindCSS utility classes for rapid development
- **Component Classes**: Custom CSS classes for complex patterns
- **Responsive**: Mobile-first responsive design
- **Accessibility**: Proper focus states and semantic HTML
- **Performance**: Optimized CSS with PurgeCSS in production 
