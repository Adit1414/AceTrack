import React from "react";
import jeeSyllabus from "../data/jeeSyllabus";

function ProgressSelector({ completedTopics, setCompletedTopics }) {
  const toggleTopic = (topic) => {
    setCompletedTopics((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]
    );
  };

  // Group topics by subject
  const groupedTopics = jeeSyllabus.reduce((groups, topic) => {
    const [subject] = topic.split(":");
    if (!groups[subject]) groups[subject] = [];
    groups[subject].push(topic);
    return groups;
  }, {});

  return (
    <div>
      <label className="block font-semibold mb-3 text-gray-700">
        Select Completed Topics:
      </label>
      <div className="space-y-4 max-h-60 overflow-y-auto p-2">
        {Object.entries(groupedTopics).map(([subject, topics]) => (
          <div key={subject} className="bg-gray-50 p-3 rounded-lg">
            <h4 className="font-bold text-red-600 mb-3">{subject}</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {topics.map((topic) => (
                <label
                  key={topic}
                  className="flex items-center gap-2 text-base p-2 hover:bg-gray-100 rounded"
                >
                  <input
                    type="checkbox"
                    checked={completedTopics.includes(topic)}
                    onChange={() => toggleTopic(topic)}
                    className="h-5 w-5 text-red-600 rounded focus:ring-red-500 border-gray-300"
                  />
                  <span>{topic.split(":")[1].trim()}</span>
                </label>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ProgressSelector;