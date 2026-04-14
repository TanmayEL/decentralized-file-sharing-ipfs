import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { useAuth } from '../../context/AuthContext';
import { toast } from 'react-toastify';

function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
    toast.success('Logged out successfully!');
  };

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          IPFS File Sharing
        </Typography>
        {isAuthenticated ? (
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Typography variant="body1" sx={{ alignSelf: 'center' }}>
              Welcome, {user?.username}!
            </Typography>
            <Button color="inherit" onClick={() => navigate('/')}>Dashboard</Button>
            <Button color="inherit" onClick={() => navigate('/upload')}>Upload</Button>
            <Button color="inherit" onClick={() => navigate('/public')}>Public Files</Button>
            <Button color="inherit" onClick={handleLogout}>Logout</Button>
          </Box>
        ) : (
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button color="inherit" onClick={() => navigate('/')}>Home</Button>
            <Button color="inherit" onClick={() => navigate('/public')}>Public Files</Button>
            <Button color="inherit" onClick={() => navigate('/login')}>Login</Button>
            <Button color="inherit" onClick={() => navigate('/register')}>Register</Button>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
}

export default Navbar;
