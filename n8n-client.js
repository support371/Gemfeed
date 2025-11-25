const axios = require('axios');

class N8NClient {
  constructor(baseURL) {
    this.baseURL = baseURL.replace(/\/$/, '');
    this.client = axios.create({ baseURL: this.baseURL, timeout: 30000 });
  }

  async triggerWorkflow(workflowId, data = {}) {
    try {
      const response = await this.client.post(`/webhook/${workflowId}`, data);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async generateContent(topic, platforms = ['twitter']) {
    return await this.triggerWorkflow('content-generator', {
      topic,
      platforms,
      timestamp: new Date().toISOString(),
      source: 'replit'
    });
  }

  async processRSS(feedUrl, action = 'summarize') {
    return await this.triggerWorkflow('rss-processor', {
      feed_url: feedUrl,
      action: action,
      output_format: 'social_media',
      source: 'replit'
    });
  }
}

const n8n = new N8NClient('http://34.83.140.18:5678');
module.exports = { n8n };
