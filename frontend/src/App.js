import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, Container, Typography, Button } from '@mui/material';
import { useAuth } from './context/AuthContext';
import Navbar from './components/common/Navbar';
import Dashboard from './components/files/Dashboard';
import FileUpload from './components/files/FileUpload';
import PublicFiles from './components/files/PublicFiles';
import Login from './components/auth/Login';
import Register from './components/auth/Register';

function HomePage() {
  return (
    <Container maxWidth="md" sx={{ mt: 8, textAlign: 'center' }}>
      <Typography variant="h2" component="h1" gutterBottom>
        🌐 IPFS File Sharing Platform
      </Typography>
      <Typography variant="h5" color="text.secondary" paragraph>
        Decentralized file storage and sharing powered by IPFS
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Upload, share, and collaborate on files stored on the InterPlanetary File System.
        Experience true decentralization with censorship-resistant file storage.
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
        <Button variant="contained" size="large" onClick={() => window.location.href = '/login'}>
          Get Started
        </Button>
        <Button variant="outlined" size="large" onClick={() => window.location.href = '/public'}>
          Browse Public Files
        </Button>
      </Box>
    </Container>
  );
}

function App() {
  const { user } = useAuth();

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Navbar />
      <Routes>
        <Route path="/" element={user ? <Dashboard /> : <HomePage />} />
        <Route path="/upload" element={user ? <FileUpload /> : <Navigate to="/login" />} />
        <Route path="/public" element={<PublicFiles />} />
        <Route path="/login" element={user ? <Navigate to="/" /> : <Login />} />
        <Route path="/register" element={user ? <Navigate to="/" /> : <Register />} />
      </Routes>
    </Box>
  );
}

export default App;
