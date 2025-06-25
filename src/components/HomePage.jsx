import { useState } from "react";
import jeeSyllabus from "../data/jeeSyllabus";
import ExamSelector from "./ExamSelector";
import TimeSelector from "./TimeSelector";
import { Button } from "./Button";
import "../styles/home.css";
import "../styles/modal.css";
import "../styles/form.css";

export default function HomePage() {
  const [selectedExam, setSelectedExam] = useState("JEE Mains");
  const [timeLeft, setTimeLeft] = useState({ value: 30, unit: "days" });
  const [completedTopics, setCompletedTopics] = useState([]);
  const [showProgressModal, setShowProgressModal] = useState(false);

  const handleGenerate = () => {
    setShowProgressModal(false);
    // Handle plan generation logic here
  };

  return (
    <div className="study-planner-container">
      <div className="study-planner-card">
        <h1 className="study-planner-title">Study Planner</h1>
        
        <div className="study-planner-form">
          <ExamSelector 
            selectedExam={selectedExam} 
            setSelectedExam={setSelectedExam} 
          />
          
          <TimeSelector 
            timeLeft={timeLeft} 
            setTimeLeft={setTimeLeft} 
          />
          
          <button
            onClick={() => setShowProgressModal(true)}
            className="btn btn-primary btn-block btn-lg"
          >
            Continue
          </button>
        </div>
      </div>

      {/* Progress Selection Modal */}
      {showProgressModal && (
        <div className="progress-modal-overlay">
          <div className="progress-modal-content">
            <div className="progress-modal-header">
              <h2 className="progress-modal-title">Your Progress</h2>
              <button 
                onClick={() => setShowProgressModal(false)}
                className="progress-modal-close"
              >
                &times;
              </button>
            </div>
            
            <div className="progress-list">
              {jeeSyllabus.map(topic => (
                <label key={topic} className="progress-item">
                  <input
                    type="checkbox"
                    checked={completedTopics.includes(topic)}
                    onChange={() => {
                      setCompletedTopics(prev => 
                        prev.includes(topic)
                          ? prev.filter(t => t !== topic)
                          : [...prev, topic]
                      );
                    }}
                    className="progress-checkbox"
                  />
                  <span className="progress-label">{topic}</span>
                </label>
              ))}
            </div>
            
            <button
              onClick={handleGenerate}
              className="btn btn-primary btn-block btn-lg"
            >
              Generate Study Plan
            </button>
          </div>
        </div>
      )}
    </div>
  );
}