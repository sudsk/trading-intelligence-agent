import React from 'react';
import { actionsAPI } from '../services/api';

const ActionBar = ({ clientId, profile, onActionTaken }) => {
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
      // Get first recommendation from NBA agent
      const recommendation = profile?.recommendations?.[0];
      
      if (!recommendation) {
        showToast('❌ No recommendations available');
        return;
      }

      const products = recommendation.products || ['Product recommendation'];
      const title = `${recommendation.action.replace(/_/g, ' ')} - ${products[0]}`.substring(0, 95);
      
      await actionsAPI.create({
        client_id: clientId,
        action_type: recommendation.action,
        title: title,
        description: recommendation.message?.substring(0, 450),
        products: products.map(p => p.substring(0, 95))
      });
      
      showToast(`💼 Product proposed: ${products[0]} - logged to Insights`);

      // ✅ Trigger refresh
      if (onActionTaken) {
        onActionTaken();
      }      
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
