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
  User,
  Plus,
  Settings,
  Download,
  Loader2,
  AlertCircle,
  CheckCircle,
  X
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

interface QuestionType {
  name: string;
  description: string;
}

interface QuestionGenerationRequest {
  question_plan: { [key: string]: number };
  testing_mode: boolean;
  exam_name: string;
}

// Helper to format filename for display
const formatFilenameForDisplay = (filename: string): string => {
  if (filename.toLowerCase().includes('questions')) return 'Questions';
  if (filename.toLowerCase().includes('verifications')) return 'Verifications';
  if (filename.toLowerCase().includes('skipped')) return 'Skipped';
  return 'Download File';
};

const Dashboard: React.FC<DashboardProps> = ({ user, onLogout }) => {
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-gray-100">
        <div className="text-center">
          <div className="w-12 h-12 bg-gradient-to-r from-cyan-500 to-cyan-600 rounded-xl flex items-center justify-center mx-auto mb-4">
            <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          </div>
          <p className="text-gray-600">Loading user data...</p>
        </div>
      </div>
    );
  }
  const [currentDate, setCurrentDate] = useState(new Date());
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showQuestionGenerator, setShowQuestionGenerator] = useState(false);
  const [onboardingData, setOnboardingData] = useState<any>(null);
  
  const [questionTypes, setQuestionTypes] = useState<QuestionType[]>([]);
  const [questionPlan, setQuestionPlan] = useState<{ [key: string]: number }>({});
  const [testingMode, setTestingMode] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationResult, setGenerationResult] = useState<{
    success: boolean;
    message: string;
    files?: { [key: string]: string };
  } | null>(null);
  
  const API_BASE_URL = 'http://localhost:8000';
  
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

  useEffect(() => {
    if (showQuestionGenerator && questionTypes.length === 0) {
      loadQuestionTypes();
    }
  }, [showQuestionGenerator]);

  const loadQuestionTypes = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/api/question-types`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const types = await response.json();
        setQuestionTypes(types);
      } else {
        console.error('Failed to load question types');
      }
    } catch (error) {
      console.error('Error loading question types:', error);
    }
  };

  const handleQuestionCountChange = (questionType: string, count: string) => {
    const numCount = parseInt(count) || 0;
    setQuestionPlan(prev => ({
      ...prev,
      [questionType]: numCount
    }));
  };

  const generateQuestions = async () => {
    const totalQuestions = Object.values(questionPlan).reduce((sum, count) => sum + count, 0);
    if (totalQuestions === 0) {
      setGenerationResult({
        success: false,
        message: 'Please select at least one question type with a count greater than 0.'
      });
      return;
    }

    const invalidCounts = Object.entries(questionPlan).filter(([_, count]) => count > 0 && count % 5 !== 0);
    if (invalidCounts.length > 0) {
      setGenerationResult({
        success: false,
        message: 'All question counts must be multiples of 5.'
      });
      return;
    }

    setIsGenerating(true);
    setGenerationResult(null);

    try {
      const token = localStorage.getItem('access_token');
      const examName = onboardingData?.examName || 'General Exam';
      
      const request: QuestionGenerationRequest = {
        question_plan: Object.fromEntries(
          Object.entries(questionPlan).filter(([_, count]) => count > 0)
        ),
        testing_mode: testingMode,
        exam_name: examName
      };

      const response = await fetch(`${API_BASE_URL}/api/generate-questions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(request)
      });

      const result = await response.json();
       if (!response.ok) {
        setGenerationResult({ success: false, message: result.detail || 'An unknown error occurred on the server.' });
      } else {
        setGenerationResult(result);
      }

    } catch (error) {
      setGenerationResult({
        success: false,
        message: `An unexpected error occurred: ${error}`
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadFile = async (filename: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/api/download-questions/${filename}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        alert('Failed to download file. Please try again.');
        console.error('Failed to download file');
      }
    } catch (error) {
      alert('An error occurred while downloading the file.');
      console.error('Error downloading file:', error);
    }
  };

  // Sample data for the calendar
  const studyTasks = {
    '2025-08-22': [
      { task: 'Revise Math', duration: '2h', type: 'revision' },
      { task: 'Practice PYQs', duration: '1h', type: 'practice' }
    ],
    '2025-08-23': [
      { task: 'Physics Chapter 3', duration: '3h', type: 'study' },
      { task: 'Mock Test', duration: '2h', type: 'test' }
    ],
  };

  const streakDays = [
    '2025-08-18', '2025-08-19', '2025-08-20', '2025-08-21', '2025-08-22'
  ];

  const todaysTasks = [
    { id: 1, task: 'Read Physics Chapter 3', completed: true },
    { id: 2, task: 'Attempt 20 mock questions', completed: false },
    { id: 3, task: 'Revise last week\'s notes', completed: false },
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

    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="h-24 border border-gray-100"></div>);
    }

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
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`streak-empty-${i}`} className="h-8 w-8"></div>);
    }
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
  const completionPercentage = tasks.length > 0 ? Math.round((completedTasks / tasks.length) * 100) : 0;
  const daysUntilExam = getDaysUntilExam();
  const getUserDisplayName = () => {
    return user?.email?.split('@')[0] || 'User';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
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
                  {daysUntilExam !== null && (
                    <span className="text-xs text-cyan-600">
                      • {daysUntilExam} days left
                    </span>
                  )}
                </div>
              )}
            </div>

            <div className="hidden md:flex items-center space-x-8">
               <button className="flex items-center gap-2 px-3 py-2 rounded-lg bg-cyan-100 text-cyan-700 font-medium">
                <Home className="w-4 h-4" />
                Home
              </button>
              <button
                onClick={() => setShowQuestionGenerator(true)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:text-gray-800 hover:bg-gray-100 transition-colors"
              >
                <FileText className="w-4 h-4" />
                Generate Tests
              </button>
               <button className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:text-gray-800 hover:bg-gray-100 transition-colors">
                <BookOpen className="w-4 h-4" />
                PYQs
              </button>
            </div>

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
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                   <div className="px-4 py-2 border-b border-gray-100">
                    <p className="text-sm font-medium text-gray-900">{getUserDisplayName()}</p>
                    <p className="text-xs text-gray-500 truncate">{user?.email || 'No email'}</p>
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
          </div>
        </div>
      </nav>

      {showUserMenu && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setShowUserMenu(false)}
        ></div>
      )}

      {showQuestionGenerator && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <Settings className="w-6 h-6 text-cyan-600" />
                  <h2 className="text-xl font-bold text-gray-800">Generate Mock Test Questions</h2>
                </div>
                <button
                  onClick={() => {
                    setShowQuestionGenerator(false);
                    setGenerationResult(null);
                    setQuestionPlan({});
                  }}
                  className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <X className="w-5 h-5 text-gray-600" />
                </button>
              </div>

              {onboardingData?.examName && (
                <div className="mb-6 p-4 bg-cyan-50 rounded-lg border border-cyan-200">
                  <p className="text-sm text-cyan-700">
                    <strong>Target Exam:</strong> {onboardingData.examName}
                  </p>
                </div>
              )}

              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Select Question Types</h3>
                <div className="space-y-4">
                  {questionTypes.length > 0 ? questionTypes.map((qtype) => (
                    <div key={qtype.name} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-cyan-300 transition-colors">
                      <div>
                        <h4 className="font-medium text-gray-800">{qtype.name}</h4>
                        <p className="text-sm text-gray-600">{qtype.description}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          min="0"
                          step="5"
                          placeholder="0"
                          value={questionPlan[qtype.name] || ''}
                          onChange={(e) => handleQuestionCountChange(qtype.name, e.target.value)}
                          className="w-20 px-3 py-2 border border-gray-300 rounded-lg text-center focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                        />
                      </div>
                    </div>
                  )) : <p className="text-gray-500">Loading question types...</p>}
                </div>
              </div>

              <div className="mb-6">
                <label className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:border-cyan-300 transition-colors cursor-pointer">
                  <input
                    type="checkbox"
                    checked={testingMode}
                    onChange={(e) => setTestingMode(e.target.checked)}
                    className="w-4 h-4 text-cyan-600 border-gray-300 rounded focus:ring-cyan-500"
                  />
                  <div>
                    <h4 className="font-medium text-gray-800">Testing Mode</h4>
                    <p className="text-sm text-gray-600">Generate sample questions for testing (faster, uses mock data).</p>
                  </div>
                </label>
              </div>

              {generationResult && (
                <div className={`mb-6 p-4 rounded-lg border ${
                  generationResult.success 
                    ? 'bg-green-50 border-green-200' 
                    : 'bg-red-50 border-red-200'
                }`}>
                  <div className="flex items-center gap-2 mb-2">
                    {generationResult.success ? <CheckCircle className="w-5 h-5 text-green-600" /> : <AlertCircle className="w-5 h-5 text-red-600" />}
                    <span className={`font-medium ${generationResult.success ? 'text-green-800' : 'text-red-800'}`}>
                      {generationResult.success ? 'Success!' : 'Error'}
                    </span>
                  </div>
                  <p className={`text-sm ${generationResult.success ? 'text-green-700' : 'text-red-700'}`}>
                    {generationResult.message}
                  </p>
                  
                  {generationResult.success && generationResult.files && (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {Object.entries(generationResult.files).map(([key, filename]) => (
                        <button
                          key={key}
                          onClick={() => downloadFile(filename)}
                          className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
                        >
                          <Download className="w-4 h-4" />
                          {formatFilenameForDisplay(filename)}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div className="flex gap-3">
                <button
                  onClick={generateQuestions}
                  disabled={isGenerating}
                  className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-cyan-500 to-magenta-500 text-white rounded-lg font-medium disabled:opacity-50"
                >
                  {isGenerating ? <><Loader2 className="w-5 h-5 animate-spin" /> Generating...</> : <><Plus className="w-5 h-5" /> Generate Questions</>}
                </button>
              </div>

              <div className="mt-4 text-sm text-gray-600">
                <p><strong>Note:</strong> Question counts must be multiples of 5. Generation may take a few minutes.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          <div className="lg:col-span-3">
            <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-100">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                      <Calendar className="w-6 h-6 text-cyan-600" />
                      <h2 className="text-xl font-bold text-gray-800">Study Schedule</h2>
                    </div>
                    <div className="flex items-center gap-4">
                        <button onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1))} className="p-2 rounded-lg hover:bg-gray-100">
                            <ChevronLeft className="w-5 h-5 text-gray-600" />
                        </button>
                        <h3 className="text-lg font-semibold text-gray-800 w-36 text-center">
                            {currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                        </h3>
                        <button onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1))} className="p-2 rounded-lg hover:bg-gray-100">
                            <ChevronRight className="w-5 h-5 text-gray-600" />
                        </button>
                    </div>
                </div>
                <div className="grid grid-cols-7 gap-0 border border-gray-200 rounded-lg overflow-hidden">
                    {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                        <div key={day} className="bg-gray-50 p-3 text-center text-sm font-medium text-gray-700 border-b">{day}</div>
                    ))}
                    {renderCalendar()}
                </div>
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
          <div className="space-y-6">
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
                <div className="grid grid-cols-7 gap-1 mt-4">
                    {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map(day => (
                        <div key={day} className="text-center text-xs font-medium text-gray-500 mb-1">{day}</div>
                    ))}
                    {renderStreakCalendar()}
                </div>
            </div>
             <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-100">
                <div className="flex items-center gap-3 mb-4">
                  <Clock className="w-6 h-6 text-cyan-600" />
                  <h3 className="text-lg font-bold text-gray-800">Today's Progress</h3>
                </div>
                <div className="text-center mb-4">
                  <div className="text-2xl font-bold text-cyan-600">{completionPercentage}%</div>
                  <p className="text-sm text-gray-600">completed</p>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 my-2">
                    <div className="bg-gradient-to-r from-cyan-500 to-magenta-500 h-2 rounded-full" style={{ width: `${completionPercentage}%` }}></div>
                </div>
                <div className="text-center text-sm text-gray-600">{completedTasks} of {tasks.length} tasks done</div>
            </div>
          </div>
        </div>
        <div className="mt-8 bg-white rounded-2xl shadow-xl p-6 border">
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
                {tasks.map(task => (
                    <div key={task.id} onClick={() => toggleTask(task.id)} className={`p-4 rounded-xl border-2 cursor-pointer transition-all duration-200 ${task.completed ? 'bg-cyan-50 border-cyan-200 text-cyan-800' : 'bg-white border-gray-200 hover:border-cyan-300'}`}>
                        <div className="flex items-center gap-3">
                            {task.completed ? <CheckCircle2 className="w-5 h-5 text-cyan-600 flex-shrink-0" /> : <Circle className="w-5 h-5 text-gray-400 flex-shrink-0" />}
                            <span className={`${task.completed ? 'line-through text-cyan-700' : 'text-gray-800'} font-medium`}>{task.task}</span>
                        </div>
                    </div>
                ))}
            </div>
             {completedTasks === tasks.length && tasks.length > 0 && (
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
  );
};

export default Dashboard;