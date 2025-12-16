import React from 'react';
import { actionsAPI } from '../services/api';

const ActionBar = ({ clientId }) => {
  const [toast, setToast] = React.useState(null);

  const showToast = (message) => {
    setToast(message);
    setTimeout(() => setToast(null), 3000);
  };

  const handleCreateTask = () => {
    showToast(`📝 Task created: Follow up on ${clientId} switch risk`);
  };

  const handleShareSummary = () => {
    showToast('📤 Summary shared with team');
  };

  const handleProposeProduct = async () => {
    try {
      await actionsAPI.create({
        client_id: clientId,  // ← snake_case
        action_type: 'PROPOSE_PRODUCT',
        title: 'EURUSD Forward Strip Proposal',  // ← Added title
        description: 'Proposed forward strip to address EUR concentration risk',
        products: ['EURUSD Forward Strip', 'Options Collar']  // ← Array
      });
      showToast('💼 Product proposed: EURUSD forward strip - logged to Insights');
    } catch (error) {
      console.error('Error proposing product:', error);
      showToast('❌ Error proposing product');
    }
  };

  return (
    <>
      <div className="action-bar">
        <button className="action-btn btn-secondary" onClick={handleCreateTask}>
          📝 Create Task
        </button>
        <button className="action-btn btn-secondary" onClick={handleShareSummary}>
          📤 Share Summary
        </button>
        <button className="action-btn btn-primary" onClick={handleProposeProduct}>
          💼 Propose Product
        </button>
      </div>

      {toast && (
        <div className="toast show">
          {toast}
        </div>
      )}
    </>
  );
};

export default ActionBar;
