import React from 'react';

const App: React.FC = () => {
  return (
    <div style={{ padding: '20px' }}>
      <h1>Building Measurements - Frontend Test</h1>
      <p>If you can see this, the React app is working!</p>
      <button onClick={() => alert('Button clicked!')}>
        Test Button
      </button>
    </div>
  );
};

export default App;