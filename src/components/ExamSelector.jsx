import React from "react";

export default function ExamSelector({ selectedExam, setSelectedExam }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Select Exam
      </label>
      <select
        value={selectedExam}
        onChange={(e) => setSelectedExam(e.target.value)}
        className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
      >
        <option value="JEE Mains">JEE Mains</option>
        <option disabled>NEET (Coming Soon)</option>
        <option disabled>UGC NET (Coming Soon)</option>
        <option disabled>CAT (Coming Soon)</option>
      </select>
    </div>
  );
}