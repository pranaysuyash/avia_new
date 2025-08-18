import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const supportApi = {
  // Support Tickets
  createTicket: (data: FormData) => 
    api.post('/support/tickets', data, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
  
  getMyTickets: () => 
    api.get('/support/tickets/my'),
  
  getTicket: (ticketId: string) => 
    api.get(`/support/tickets/${ticketId}`),
  
  addTicketReply: (ticketId: string, data: { message: string; is_agent: boolean }) => 
    api.post(`/support/tickets/${ticketId}/reply`, data),
  
  rateTicket: (ticketId: string, rating: number) => 
    api.post(`/support/tickets/${ticketId}/rate`, { rating }),
  
  // Live Chat
  startChatSession: () => 
    api.post('/support/chat/start'),
  
  sendChatMessage: (sessionId: string, data: FormData) => 
    api.post(`/support/chat/${sessionId}/message`, data, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
  
  emailChatTranscript: (sessionId: string) => 
    api.post(`/support/chat/${sessionId}/email-transcript`),
  
  // Help Articles
  getHelpArticles: (category?: string) => 
    api.get('/support/help/articles', { params: { category } }),
  
  searchHelpArticles: (query: string, category?: string | null) => 
    api.get('/support/help/articles/search', { params: { query, category } }),
  
  getHelpArticle: (articleId: string) => 
    api.get(`/support/help/articles/${articleId}`),
  
  rateHelpArticle: (articleId: string, helpful: boolean) => 
    api.post(`/support/help/articles/${articleId}/rate`, { helpful }),
  
  // FAQ
  getFAQs: (category?: string) => 
    api.get('/support/faq', { params: { category } }),
  
  // Tutorials
  getTutorials: (type?: string, difficulty?: string) => 
    api.get('/support/tutorials', { params: { type, difficulty } }),
  
  getTutorial: (tutorialId: string) => 
    api.get(`/support/tutorials/${tutorialId}`),
  
  trackTutorialProgress: (tutorialId: string, progress: number) => 
    api.post(`/support/tutorials/${tutorialId}/progress`, { progress }),
  
  getLearningPath: (userType: string) => 
    api.get(`/support/tutorials/learning-path/${userType}`),
  
  // Community Forum
  getForumPosts: (category?: string, solved?: boolean) => 
    api.get('/support/forum/posts', { params: { category, solved } }),
  
  searchForumPosts: (query: string, category?: string) => 
    api.get('/support/forum/posts/search', { params: { query, category } }),
  
  createForumPost: (data: {
    title: string;
    content: string;
    category: string;
    tags: string[];
  }) => api.post('/support/forum/posts', data),
  
  getForumPost: (postId: string) => 
    api.get(`/support/forum/posts/${postId}`),
  
  replyToForumPost: (postId: string, content: string) => 
    api.post(`/support/forum/posts/${postId}/reply`, { content }),
  
  upvoteForumPost: (postId: string) => 
    api.post(`/support/forum/posts/${postId}/upvote`),
  
  markPostAsSolved: (postId: string, answerId: string) => 
    api.post(`/support/forum/posts/${postId}/solved`, { answer_id: answerId }),
  
  // Feedback
  submitFeedback: (data: {
    category: string;
    subject: string;
    description: string;
    rating?: number;
  }) => api.post('/support/feedback', data),
  
  getMyFeedback: () => 
    api.get('/support/feedback/my'),
  
  // Feature Requests
  createFeatureRequest: (data: {
    title: string;
    description: string;
  }) => api.post('/support/feature-requests', data),
  
  getFeatureRequests: (status?: string) => 
    api.get('/support/feature-requests', { params: { status } }),
  
  upvoteFeatureRequest: (requestId: string) => 
    api.post(`/support/feature-requests/${requestId}/upvote`),
  
  commentOnFeatureRequest: (requestId: string, comment: string) => 
    api.post(`/support/feature-requests/${requestId}/comment`, { comment }),
  
  // Support Dashboard
  getSupportDashboard: () => 
    api.get('/support/dashboard'),
  
  getUserSupportHistory: () => 
    api.get('/support/history'),
  
  // Search all resources
  searchAllResources: (query: string) => 
    api.get('/support/search', { params: { query } }),
};

export default supportApi;