import React, { useState, useEffect } from 'react';
import { clientsAPI } from './services/api';
import { useSSE } from './hooks/useSSE';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
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
  const [alert, setAlert] = useState(null);

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
    }
  }, [sseData]);

  const loadClients = async () => {
    try {
      const response = await clientsAPI.getAll();
      setClients(response.data);
      if (response.data.length > 0) {
        selectClient(response.data[0].clientId);
      }
    } catch (error) {
      console.error('Error loading clients:', error);
    }
  };

  const selectClient = async (clientId) => {
    setLoading(true);
    try {
      const [profileRes, timelineRes, insightsRes, mediaRes] = await Promise.all([
        clientsAPI.getProfile(clientId),
        clientsAPI.getTimeline(clientId),
        clientsAPI.getInsights(clientId),
        clientsAPI.getMedia(clientId),
      ]);

      setSelectedClient(clientId);
      setProfile({
        ...profileRes.data,
        timeline: timelineRes.data,
        insights: insightsRes.data,
        media: mediaRes.data,
      });
    } catch (error) {
      console.error('Error loading profile:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <Header onForceEvent={() => {/* trigger demo event */}} />
      <div className="main-container">
        <Sidebar 
          clients={clients} 
          selectedClient={selectedClient}
          onSelectClient={selectClient}
        />
        <div className="content">
          {alert && <AlertBanner alert={alert} onDismiss={() => setAlert(null)} />}
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
