const { n8n } = require('./n8n-client');

console.log('🚀 n8n Replit Agents Starting...\n');

async function testConnection() {
  console.log('🔗 Testing n8n connection...');
  const test = await n8n.triggerWorkflow('test', { message: 'Hello from Replit!' });
  
  if (test.success) {
    console.log('✅ n8n connection successful!');
    console.log('🎯 Your agents are ready to use!');
    console.log('\n🤖 Available commands:');
    console.log('   await n8n.generateContent("AI News", ["twitter", "linkedin"])');
    console.log('   await n8n.processRSS("https://techcrunch.com/feed/")');
    console.log('   await n8n.triggerWorkflow("your-workflow-id", {data: "here"})');
  } else {
    console.log('❌ n8n connection failed:');
    console.log('   Make sure n8n is running at: http://34.83.140.18:5678');
    console.log('   Check if workflows are created in n8n interface');
  }
}

testConnection();
