import React, { useState, useEffect } from 'react';
import LoginPage from './components/LoginPage';
import SignupPage from './components/SignupPage';
import OnboardingPage from './components/OnboardingPage';
import Dashboard from './components/Dashboard';

// Types for user data
interface User {
  id: number;
  email: string;
  token?: string;
  hasCompletedOnboarding?: boolean;
}

interface OnboardingData {
  examName: string;
  examDate: string;
  topicsCovered: string[];
  studyHours: string;
  studyDays: string;
}

const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [showSignup, setShowSignup] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showOnboarding, setShowOnboarding] = useState(false);

  // Check if user is already logged in when app loads
  useEffect(() => {
    const checkExistingAuth = () => {
      const token = localStorage.getItem('access_token');
      const userData = localStorage.getItem('user_data');
      
      if (token && userData) {
        try {
          const parsedUser = JSON.parse(userData);
          const userWithToken = { ...parsedUser, token };
          setUser(userWithToken);
          
          // Check if user has completed onboarding
          const onboardingData = localStorage.getItem('onboarding_data');
          if (!onboardingData) {
            setShowOnboarding(true);
          }
        } catch (error) {
          // If parsing fails, clear invalid data
          localStorage.removeItem('access_token');
          localStorage.removeItem('user_data');
          localStorage.removeItem('onboarding_data');
        }
      }
      setLoading(false);
    };

    checkExistingAuth();
  }, []);

  // Handle successful login
  const handleLogin = (userData: { id: number; email: string; token: string }) => {
    const user: User = {
      id: userData.id,
      email: userData.email,
      token: userData.token
    };
    
    setUser(user);
    
    // Store user data in localStorage (without token for security)
    localStorage.setItem('user_data', JSON.stringify({
      id: user.id,
      email: user.email
    }));
    
    // Check if user needs onboarding
    const onboardingData = localStorage.getItem('onboarding_data');
    if (!onboardingData) {
      setShowOnboarding(true);
    }
  };

  // Handle successful signup
  const handleSignup = (userData: { id: number; email: string }) => {
    console.log('User account created:', userData);
    // After successful signup, switch to login page
    setShowSignup(false);
  };

  // Handle onboarding completion
  const handleOnboardingComplete = async (onboardingData: OnboardingData) => {
    try {
      // Store onboarding data locally for now
      localStorage.setItem('onboarding_data', JSON.stringify({
        ...onboardingData,
        completedAt: new Date().toISOString()
      }));

      // TODO: Send onboarding data to backend API
      // const response = await fetch('http://localhost:8000/api/onboarding', {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json',
      //     'Authorization': `Bearer ${user?.token}`
      //   },
      //   body: JSON.stringify(onboardingData)
      // });

      // Mark onboarding as complete
      setShowOnboarding(false);
      
      // Update user state
      if (user) {
        setUser({ ...user, hasCompletedOnboarding: true });
      }

      console.log('Onboarding completed with data:', onboardingData);
    } catch (error) {
      console.error('Error completing onboarding:', error);
      // For now, still proceed to dashboard even if API call fails
      setShowOnboarding(false);
    }
  };

  // Handle logout
  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');
    localStorage.removeItem('onboarding_data');
    setShowSignup(false);
    setShowOnboarding(false);
  };

  // Handle going back from onboarding
  const handleOnboardingBack = () => {
    // For now, just complete onboarding with empty data
    // In a real app, you might want to allow partial saves
    setShowOnboarding(false);
  };

  // Handle switching between login and signup
  const switchToSignup = () => setShowSignup(true);
  const switchToLogin = () => setShowSignup(false);

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-cyan-50 via-white to-purple-50">
        <div className="text-center">
          <div className="w-12 h-12 bg-gradient-to-r from-cyan-500 to-cyan-600 rounded-xl flex items-center justify-center mx-auto mb-4 animate-pulse">
            <span className="text-white font-bold">A</span>
          </div>
          <p className="text-gray-600">Loading AceTrack...</p>
        </div>
      </div>
    );
  }

  // If user is logged in but needs onboarding
  if (user && showOnboarding) {
    return (
      <div className="bg-gradient-to-br from-cyan-50 via-white to-purple-50 min-h-screen">
        <OnboardingPage 
          onBack={handleOnboardingBack}
          onComplete={handleOnboardingComplete}
        />
      </div>
    );
  }

  // If user is logged in and has completed onboarding, show dashboard
  if (user && !showOnboarding) {
    return <Dashboard user={user} onLogout={handleLogout} />;
  }

  // If user is not logged in, show login or signup page
  return (
    <div className="bg-gradient-to-br from-cyan-50 via-white to-purple-50 min-h-screen">
      {showSignup ? (
        <SignupPage 
          onSignup={handleSignup}
          onSwitchToLogin={switchToLogin}
        />
      ) : (
        <LoginPage 
          onLogin={handleLogin}
          onSwitchToSignup={switchToSignup}
        />
      )}
    </div>
  );
};

export default App;