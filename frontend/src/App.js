import React, { useState, useEffect } from 'react';
import { clientsAPI } from './services/api';
import { useSSE } from './hooks/useSSE';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import AlertBanner from './components/AlertBanner'; 
import ProfileCard from './components/ProfileCard';
import MediaRibbon from './components/MediaRibbon';
import Timeline from './components/Timeline';
import InsightsFeed from './components/InsightsFeed';
import ActionBar from './components/ActionBar';
import './styles/loveship-dark.css';

function App() {
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false); 
  const [alert, setAlert] = useState(null);
  const [profileCache, setProfileCache] = useState({}); 

  // SSE for real-time alerts
  const { data: sseData } = useSSE(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/alerts/stream`);

  useEffect(() => {
    loadClients();
  }, []);

  useEffect(() => {
    if (sseData && sseData.type === 'switch_probability_alert') {
      setAlert(sseData);
      // Update client in list if matches
      setClients(prev => prev.map(c => 
        c.clientId === sseData.clientId 
          ? { ...c, switchProb: sseData.newSwitchProb }
          : c
      ));
      // Clear cache for this client to force refresh on next view
      setProfileCache(prev => {
        const updated = { ...prev };
        delete updated[sseData.clientId];
        return updated;
      });  
      
      // Auto-refresh profile if it's the currently selected client
      if (sseData.clientId === selectedClient) {
        selectClient(selectedClient);
      }
    }
  }, [sseData, selectedClient]);

  const loadClients = async () => {
    try {
      const response = await clientsAPI.getAll();
      console.log('API response:', response.data);
      const { clients } = response.data;  
      setClients(clients);
      if (clients.length > 0) {
        selectClient(clients[0].client_id);
      }
    } catch (error) {
      console.error('Error loading clients:', error);
    }
  };

  const selectClient = async (clientId) => {
    if (loading) {
      console.log('Already loading, skipping...');
      return;
    }
    
    if (profileCache[clientId]) {
      console.log('Using cached profile for', clientId);
      setSelectedClient(clientId);
      setProfile(profileCache[clientId]);
      return;
    }

    console.log('Loading profile from database for', clientId);
    setLoading(true);
    try {
      // All 3 calls return instant data from database
      const [profileRes, timelineRes, insightsRes] = await Promise.all([
        clientsAPI.getProfile(clientId),
        clientsAPI.getTimeline(clientId),
        clientsAPI.getInsights(clientId),
      ]);    

      const fullProfile = {
        ...profileRes.data,
        timeline: timelineRes.data.timeline,
        insights: insightsRes.data.insights,
      };
      
      setSelectedClient(clientId);
      setProfile(fullProfile);
  
      setProfileCache(prev => ({
        ...prev,
        [clientId]: fullProfile
      }));
      
    } catch (error) {
      console.error('Error loading profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const refreshProfile = async () => {
    if (!selectedClient || loading) return;
    
    console.log('🔄 Triggering fresh analysis for', selectedClient);
    setLoading(true);
    
    try {
      // Step 1: Trigger agent analysis (20s)
      await clientsAPI.triggerAnalysis(selectedClient, {
        timeout: 90000  // 90 seconds in milliseconds
      });
      console.log('✅ Analysis complete, fetching updated data...');
      
      // Step 2: Clear cache for this client
      setProfileCache(prev => {
        const updated = { ...prev };
        delete updated[selectedClient];
        return updated;
      });
      
      // Step 3: Reload from database (now has fresh data)
      await selectClient(selectedClient);
      
    } catch (error) {
      console.error('❌ Error refreshing profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleForceEvent = async () => {
    if (!selectedClient) {
      // Optional: show toast notification
      console.warn('No client selected');
      return;
    }
  
    setIsAnalyzing(true);
    
    try {
      console.log(`🚨 Force Event triggered for: ${selectedClient}`);
      
      const response = await clientsAPI.post('/demo/trigger-alert', {
        client_id: selectedClient
      });
      
      console.log('Force Event response:', response.data);
      
      // Alert will arrive via SSE automatically
      // Profile will auto-update when SSE alert is received
      
    } catch (error) {
      console.error('Error triggering Force Event:', error);
      // Optional: show error notification
    } finally {
      setIsAnalyzing(false);
    }
  };
  
  return (
    <div className="app">
      <Header 
        onForceEvent={handleForceEvent}
        isAnalyzing={isAnalyzing}  
      />
      <div className="main-container">
        <Sidebar 
          clients={clients} 
          selectedClient={selectedClient}
          onSelectClient={selectClient}
        />
        <div className="content">
          {alert && <AlertBanner alert={alert} onDismiss={() => setAlert(null)} />}

          {isAnalyzing && (
            <div className="analyzing-overlay">
              <div className="analyzing-content">
                <div className="spinner"></div>
                <p className="analyzing-title">Running fresh analysis...</p>
                <p className="analyzing-subtext">Analyzing trades, positions, and media (~20s)</p>
              </div>
            </div>
          )}

          {loading ? (
            <div className="loading"><div className="spinner"></div></div>
          ) : profile ? (
            <>
              <ProfileCard profile={profile} /> 
              <MediaRibbon media={profile.media} />
              <Timeline timeline={profile.timeline} />
              <InsightsFeed insights={profile.insights} />
              <ActionBar clientId={selectedClient} />
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export default App;
