import React, { useState, useEffect } from 'react';
import { 
  Home, 
  Info, 
  Mail, 
  FileText, 
  BookOpen, 
  ChevronLeft, 
  ChevronRight, 
  Flame,
  CheckCircle2,
  Circle,
  Calendar,
  Clock,
  Target,
  LogOut,
  User
} from 'lucide-react';

interface User {
  id: number;
  email: string;
  token?: string;
}

interface DashboardProps {
  user: User;
  onLogout: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ user, onLogout }) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [onboardingData, setOnboardingData] = useState<any>(null);
  
  // Load onboarding data on component mount
  useEffect(() => {
    const savedOnboardingData = localStorage.getItem('onboarding_data');
    if (savedOnboardingData) {
      try {
        setOnboardingData(JSON.parse(savedOnboardingData));
      } catch (error) {
        console.error('Error parsing onboarding data:', error);
      }
    }
  }, []);

  // Sample data for the calendar
  const studyTasks = {
    '2025-01-15': [
      { task: 'Revise Math', duration: '2h', type: 'revision' },
      { task: 'Practice PYQs', duration: '1h', type: 'practice' }
    ],
    '2025-01-16': [
      { task: 'Physics Chapter 3', duration: '3h', type: 'study' },
      { task: 'Mock Test', duration: '2h', type: 'test' }
    ],
    '2025-01-17': [
      { task: 'Chemistry Lab', duration: '2h', type: 'study' },
      { task: 'Previous Papers', duration: '1h', type: 'practice' }
    ],
    '2025-01-18': [
      { task: 'Biology Review', duration: '2h', type: 'revision' },
      { task: 'Mock Questions', duration: '1h', type: 'practice' }
    ],
    '2025-01-19': [
      { task: 'Math Problems', duration: '3h', type: 'practice' },
      { task: 'Theory Notes', duration: '1h', type: 'study' }
    ]
  };

  // Sample streak data
  const streakDays = [
    '2025-01-10', '2025-01-11', '2025-01-12', '2025-01-13', '2025-01-14'
  ];

  // Today's tasks
  const todaysTasks = [
    { id: 1, task: 'Read Physics Chapter 3', completed: true },
    { id: 2, task: 'Attempt 20 mock questions', completed: false },
    { id: 3, task: 'Revise last week\'s notes', completed: false },
    { id: 4, task: 'Complete Chemistry worksheet', completed: true },
    { id: 5, task: 'Practice Math derivatives', completed: false }
  ];

  const [tasks, setTasks] = useState(todaysTasks);

  const toggleTask = (id: number) => {
    setTasks(tasks.map(task => 
      task.id === id ? { ...task, completed: !task.completed } : task
    ));
  };

  const getTaskTypeColor = (type: string) => {
    switch (type) {
      case 'study': return 'bg-cyan-100 text-cyan-700 border-cyan-200';
      case 'practice': return 'bg-magenta-100 text-magenta-700 border-magenta-200';
      case 'revision': return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'test': return 'bg-orange-100 text-orange-700 border-orange-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getDaysInMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const formatDateKey = (year: number, month: number, day: number) => {
    return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  };

  const isStreakDay = (dateKey: string) => {
    return streakDays.includes(dateKey);
  };

  const getDaysUntilExam = () => {
    if (!onboardingData?.examDate) return null;
    const today = new Date();
    const examDate = new Date(onboardingData.examDate);
    const diffTime = examDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays > 0 ? diffDays : 0;
  };

  const renderCalendar = () => {
    const daysInMonth = getDaysInMonth(currentDate);
    const firstDay = getFirstDayOfMonth(currentDate);
    const days = [];
    const today = new Date();
    const isCurrentMonth = currentDate.getMonth() === today.getMonth() && 
                          currentDate.getFullYear() === today.getFullYear();

    // Empty cells for days before the first day of the month
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="h-24 border border-gray-100"></div>);
    }

    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const dateKey = formatDateKey(currentDate.getFullYear(), currentDate.getMonth(), day);
      const dayTasks = studyTasks[dateKey] || [];
      const isToday = isCurrentMonth && day === today.getDate();

      days.push(
        <div
          key={day}
          className={`h-24 border border-gray-100 p-1 ${
            isToday ? 'bg-cyan-50 border-cyan-200' : 'bg-white hover:bg-gray-50'
          } transition-colors cursor-pointer`}
        >
          <div className={`text-sm font-medium mb-1 ${
            isToday ? 'text-cyan-700' : 'text-gray-700'
          }`}>
            {day}
          </div>
          <div className="space-y-1">
            {dayTasks.slice(0, 2).map((task, index) => (
              <div
                key={index}
                className={`text-xs px-1 py-0.5 rounded border ${getTaskTypeColor(task.type)} truncate`}
              >
                {task.task} - {task.duration}
              </div>
            ))}
            {dayTasks.length > 2 && (
              <div className="text-xs text-gray-500">+{dayTasks.length - 2} more</div>
            )}
          </div>
        </div>
      );
    }

    return days;
  };

  const renderStreakCalendar = () => {
    const daysInMonth = getDaysInMonth(currentDate);
    const firstDay = getFirstDayOfMonth(currentDate);
    const days = [];

    // Empty cells for days before the first day of the month
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`streak-empty-${i}`} className="h-8 w-8"></div>);
    }

    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const dateKey = formatDateKey(currentDate.getFullYear(), currentDate.getMonth(), day);
      const hasStreak = isStreakDay(dateKey);

      days.push(
        <div
          key={day}
          className="h-8 w-8 flex items-center justify-center text-xs relative"
        >
          <span className={`${hasStreak ? 'text-white font-medium' : 'text-gray-600'}`}>
            {day}
          </span>
          {hasStreak && (
            <div className="absolute inset-0 bg-gradient-to-r from-magenta-500 to-cyan-500 rounded-full animate-pulse"></div>
          )}
          {hasStreak && (
            <CheckCircle2 className="absolute inset-0 w-8 h-8 text-white z-10" />
          )}
        </div>
      );
    }

    return days;
  };

  const completedTasks = tasks.filter(task => task.completed).length;
  const completionPercentage = Math.round((completedTasks / tasks.length) * 100);
  const daysUntilExam = getDaysUntilExam();

  const getUserDisplayName = () => {
    return user.email.split('@')[0] || 'User';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-r from-cyan-500 to-cyan-600 rounded-lg flex items-center justify-center">
                <Target className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-bold text-gray-900">AceTrack</h1>
              {onboardingData?.examName && (
                <div className="hidden sm:flex items-center gap-2 ml-4 px-3 py-1 bg-cyan-50 rounded-full">
                  <span className="text-sm text-cyan-700">
                    📚 {onboardingData.examName.split('(')[0].trim()}
                  </span>
                  {daysUntilExam && (
                    <span className="text-xs text-cyan-600">
                      • {daysUntilExam} days left
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Navigation Links */}
            <div className="hidden md:flex items-center space-x-8">
              <button className="flex items-center gap-2 px-3 py-2 rounded-lg bg-cyan-100 text-cyan-700 font-medium">
                <Home className="w-4 h-4" />
                Home
              </button>
              <button className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:text-gray-800 hover:bg-gray-100 transition-colors">
                <Info className="w-4 h-4" />
                About
              </button>
              <button className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:text-gray-800 hover:bg-gray-100 transition-colors">
                <Mail className="w-4 h-4" />
                Contact Us
              </button>
              <button className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:text-gray-800 hover:bg-gray-100 transition-colors">
                <FileText className="w-4 h-4" />
                Mock Tests
              </button>
              <button className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:text-gray-800 hover:bg-gray-100 transition-colors">
                <BookOpen className="w-4 h-4" />
                PYQs
              </button>
            </div>

            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:text-gray-800 hover:bg-gray-100 transition-colors"
              >
                <User className="w-4 h-4" />
                <span className="hidden sm:inline">{getUserDisplayName()}</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Dropdown Menu */}
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                  <div className="px-4 py-2 border-b border-gray-100">
                    <p className="text-sm font-medium text-gray-900">{getUserDisplayName()}</p>
                    <p className="text-xs text-gray-500 truncate">{user.email}</p>
                  </div>
                  <button
                    onClick={onLogout}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
                  </button>
                </div>
              )}
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden">
              <button className="p-2 rounded-lg text-gray-600 hover:text-gray-800 hover:bg-gray-100">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Click outside to close user menu */}
      {showUserMenu && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setShowUserMenu(false)}
        ></div>
      )}

      {/* Exam Info Banner */}
      {onboardingData && (
        <div className="bg-gradient-to-r from-cyan-500 to-magenta-500 text-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium">
                  🎯 Target: {onboardingData.examName}
                </span>
                {daysUntilExam && (
                  <span className="text-sm">
                    📅 {daysUntilExam} days remaining
                  </span>
                )}
              </div>
              <div className="flex items-center gap-4 text-sm">
                <span>📖 {onboardingData.studyHours}h/day</span>
                <span>📊 {onboardingData.studyDays} days/week</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Main Calendar */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-100">
              {/* Calendar Header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <Calendar className="w-6 h-6 text-cyan-600" />
                  <h2 className="text-xl font-bold text-gray-800">Study Schedule</h2>
                </div>
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1))}
                    className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <ChevronLeft className="w-5 h-5 text-gray-600" />
                  </button>
                  <h3 className="text-lg font-semibold text-gray-800 min-w-[140px] text-center">
                    {currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                  </h3>
                  <button
                    onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1))}
                    className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <ChevronRight className="w-5 h-5 text-gray-600" />
                  </button>
                </div>
              </div>

              {/* Calendar Grid */}
              <div className="grid grid-cols-7 gap-0 border border-gray-200 rounded-lg overflow-hidden">
                {/* Day headers */}
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                  <div key={day} className="bg-gray-50 p-3 text-center text-sm font-medium text-gray-700 border-b border-gray-200">
                    {day}
                  </div>
                ))}
                {/* Calendar days */}
                {renderCalendar()}
              </div>

              {/* Legend */}
              <div className="flex flex-wrap gap-4 mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-cyan-500"></div>
                  <span className="text-sm text-gray-600">Study</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-magenta-500"></div>
                  <span className="text-sm text-gray-600">Practice</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-purple-500"></div>
                  <span className="text-sm text-gray-600">Revision</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-orange-500"></div>
                  <span className="text-sm text-gray-600">Test</span>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Streak Tracker */}
            <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-100">
              <div className="flex items-center gap-3 mb-4">
                <Flame className="w-6 h-6 text-magenta-600" />
                <h3 className="text-lg font-bold text-gray-800">Study Streak</h3>
              </div>
              
              <div className="text-center mb-4">
                <div className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-magenta-500 to-cyan-500">
                  🔥 {streakDays.length}
                </div>
                <p className="text-sm text-gray-600">days in a row</p>
              </div>

              {/* Mini Calendar */}
              <div className="grid grid-cols-7 gap-1">
                {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map(day => (
                  <div key={day} className="text-center text-xs font-medium text-gray-500 mb-1">
                    {day}
                  </div>
                ))}
                {renderStreakCalendar()}
              </div>
            </div>

            {/* Progress Summary */}
            <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-100">
              <div className="flex items-center gap-3 mb-4">
                <Clock className="w-6 h-6 text-cyan-600" />
                <h3 className="text-lg font-bold text-gray-800">Today's Progress</h3>
              </div>
              
              <div className="text-center mb-4">
                <div className="text-2xl font-bold text-cyan-600">
                  {completionPercentage}%
                </div>
                <p className="text-sm text-gray-600">completed</p>
              </div>

              <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                <div 
                  className="bg-gradient-to-r from-cyan-500 to-magenta-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${completionPercentage}%` }}
                ></div>
              </div>

              <div className="text-center text-sm text-gray-600">
                {completedTasks} of {tasks.length} tasks done
              </div>
            </div>
          </div>
        </div>

        {/* Today's Plan */}
        <div className="mt-8">
          <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-100">
            <div className="flex items-center gap-3 mb-6">
              <CheckCircle2 className="w-6 h-6 text-cyan-600" />
              <h2 className="text-xl font-bold text-gray-800">Today's Plan</h2>
              <div className="ml-auto text-sm text-gray-500">
                {new Date().toLocaleDateString('en-US', { 
                  weekday: 'long', 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {tasks.map(task => (
                <div
                  key={task.id}
                  className={`p-4 rounded-xl border-2 transition-all duration-200 cursor-pointer ${
                    task.completed
                      ? 'bg-cyan-50 border-cyan-200 text-cyan-800'
                      : 'bg-white border-gray-200 hover:border-cyan-300 hover:bg-cyan-50'
                  }`}
                  onClick={() => toggleTask(task.id)}
                >
                  <div className="flex items-center gap-3">
                    {task.completed ? (
                      <CheckCircle2 className="w-5 h-5 text-cyan-600 flex-shrink-0" />
                    ) : (
                      <Circle className="w-5 h-5 text-gray-400 flex-shrink-0" />
                    )}
                    <span className={`${
                      task.completed ? 'line-through text-cyan-700' : 'text-gray-800'
                    } font-medium`}>
                      {task.task}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {completedTasks === tasks.length && (
              <div className="mt-6 p-4 bg-gradient-to-r from-cyan-50 to-magenta-50 rounded-xl border border-cyan-200">
                <div className="text-center">
                  <div className="text-2xl mb-2">🎉</div>
                  <p className="text-cyan-700 font-medium">Congratulations! You've completed all tasks for today!</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;