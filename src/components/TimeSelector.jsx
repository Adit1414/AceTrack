import React from "react";

export default function TimeSelector({ timeLeft, setTimeLeft }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Time Left
      </label>
      <div className="flex gap-2">
        <input
          type="number"
          min="1"
          value={timeLeft.value}
          onChange={(e) => setTimeLeft({...timeLeft, value: e.target.value})}
          className="w-1/2 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500"
          placeholder="e.g. 30"
        />
        <select
          value={timeLeft.unit}
          onChange={(e) => setTimeLeft({...timeLeft, unit: e.target.value})}
          className="w-1/2 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500"
        >
          <option value="days">Days</option>
          <option value="weeks">Weeks</option>
          <option value="months">Months</option>
          <option value="years">Years</option>
        </select>
      </div>
    </div>
  );
}