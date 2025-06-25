export default function PopupModal({ title, children, onClose }) {
  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 relative animate-fade-in-up">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-500 hover:text-red-600 text-3xl"
        >
          &times;
        </button>
        <h2 className="text-2xl font-bold mb-6 text-center text-red-600">
          {title}
        </h2>
        <div>{children}</div>
      </div>
    </div>
  );
}