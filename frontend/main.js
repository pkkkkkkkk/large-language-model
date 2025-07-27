document.addEventListener('DOMContentLoaded', () => {
  const imageUploadBtn = document.getElementById('imageUploadBtn');
  const imageUploadInput = document.getElementById('imageUpload');
  const imagePreviewContainer = document.getElementById('imagePreviewContainer');
  // DOM Elements
  const appLayout = document.getElementById("appLayout");
  const userInput = document.getElementById("userInput");
  const chatHistory = document.getElementById("chatHistory");
  const sendButton = document.getElementById("sendButton");
  const newChatBtn = document.getElementById("newChatBtn");
  const sidebarToggle = document.getElementById("sidebarToggle");
  const historyList = document.getElementById("historyList");
  const themeToggle = document.getElementById("themeToggle"); // 新增：主题切换按钮
  const rightSidebarToggle = document.getElementById("rightSidebarToggle");


  const userInfoBtn = document.getElementById("userInfoBtn");
  const userDetails = document.getElementById("userDetails");
  const changePasswordBtn = document.getElementById("changePasswordBtn");
  const userIdDisplay = document.getElementById("userIdDisplay");
  // 新增元素引用
  const changePasswordForm = document.getElementById('changePasswordForm');
  const oldPasswordInput = document.getElementById('oldPassword');
  const newPasswordInput = document.getElementById('newPassword');
  const confirmPasswordInput = document.getElementById('confirmPassword');
  const submitPasswordBtn = document.getElementById('submitPasswordBtn');
  const cancelPasswordBtn = document.getElementById('cancelPasswordBtn');
  const logoutBtn = document.getElementById('logoutBtn');
  const micButton = document.getElementById('micButton'); // ✅ 新增麦克风按钮引用
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  // State Management
  let conversations = [];
  let activeChatId = null;
  let recognition = null; // ✅ 新增: 用于存放语音识别实例
  let isRecognizing = false; // ✅ 新增: 跟踪识别状态
  let currentAbortController = null; // 用于终止请求
  let currentLoadingElement = null; // 当前加载中的消息元素
  let speechBaseText = ''; // ✅ 新增：用于存储开始语音识别前输入框已有的文本
  const username = localStorage.getItem("username");
  // --- Initialization ---
  function init() {
    loadTheme(); // 新增：加载主题
    loadConversations();
    renderSidebar();
    fetchAndDisplayRecommendation();
    // 初始化用户信息
    initUserInfo();

    if (conversations.length > 0) {
      setActiveChat(conversations[0].id);
    } else {
      createNewChat();
    }
     if (SpeechRecognition) { // ✅ 仅在浏览器支持时才添加事件
      micButton.addEventListener('click', handleMicButtonClick);
    } else {
      micButton.style.display = 'none'; // 如果不支持，则隐藏按钮
      console.warn('您的浏览器不支持 Web Speech API');
    }
    // Event Listeners
    sendButton.addEventListener('click', () => submitInput());
    userInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        submitInput();
      }
    });
     

    userInput.addEventListener('input', autoGrow);
    newChatBtn.addEventListener('click', createNewChat);
    sidebarToggle.addEventListener('click', () => appLayout.classList.toggle('sidebar-collapsed'));
    rightSidebarToggle.addEventListener('click', () => appLayout.classList.toggle('right-sidebar-collapsed'));
    themeToggle.addEventListener('click', toggleTheme); // 新增：主题切换事件
    // 新增用户信息事件监听
    userInfoBtn.addEventListener('click', toggleUserDetails);
    changePasswordBtn.addEventListener('click', handleChangePassword);

    // 新增事件监听
    submitPasswordBtn.addEventListener('click', handlePasswordChange);
    cancelPasswordBtn.addEventListener('click', cancelPasswordChange);
    logoutBtn.addEventListener('click', logout);
  }

   function handleMicButtonClick() {
    console.log("麦克风按钮被点击了！当前识别状态: ", isRecognizing); // 增加日志
    if (isRecognizing) {
      stopSpeechRecognition();
    } else {
      startSpeechRecognition();
    }
  }

  function startSpeechRecognition() {
    if (!SpeechRecognition) {
      alert('抱歉，您的浏览器不支持语音识别功能。');
      return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = 'zh-CN'; // 设置语言为中文
    recognition.continuous = true; // 持续识别，不会因短暂静默而停止
    recognition.interimResults = true; // 返回临时结果，实现实时上屏

    speechBaseText = userInput.value ? userInput.value + ' ' : '';
    // 当识别开始时
    recognition.onstart = () => {
      isRecognizing = true;
      micButton.classList.add('listening');
      micButton.title = "正在聆听...点击停止";
      userInput.placeholder = "请开始说话…";
    };

    // 当识别到结果时
    recognition.onresult = (event) => {
      let interim_transcript = '';
      let final_transcript = '';

      // 遍历所有识别结果
      for (let i = 0; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          final_transcript += event.results[i][0].transcript;
        } else {
          interim_transcript += event.results[i][0].transcript;
        }
      }

      // 用“基础文本 + 最终识别结果 + 临时识别结果”的组合来完全覆盖输入框内容
      userInput.value = speechBaseText + final_transcript + interim_transcript;
      autoGrow.call(userInput); // 触发输入框高度自适应
    };

    recognition.onerror = (event) => {
      console.error('语音识别错误:', event.error);
      let errorMessage = "识别出错，请重试";
      if (event.error === 'not-allowed' || event.error === 'permission-denied') {
        errorMessage = "无法使用麦克风，请检查浏览器权限设置。";
        alert("您需要允许网页使用麦克风。请点击地址栏左侧的图标，检查并修改麦克风权限。");
      } else if (event.error === 'no-speech') {
        errorMessage = "没有检测到语音，请重试。";
      }
      userInput.placeholder = errorMessage;
    };

    recognition.onend = () => {
      isRecognizing = false;
      micButton.classList.remove('listening');
      micButton.title = "语音输入";
      userInput.placeholder = "问一问食悟美食助手…";
      recognition = null;
      speechBaseText = ''; // ✅ 识别结束后清空基础文本
    };

    recognition.start();
  }

  function stopSpeechRecognition() {
    if (recognition) {
      recognition.stop();
    }
  }
 
  // --- 新增：Theme Logic ---
  function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    appLayout.dataset.theme = savedTheme;
  }
  function autoGrow() {
    // 先重置高度，让 scrollHeight 能被正确计算
    this.style.height = 'auto';
    // 将高度设置为内容的实际高度
    this.style.height = (this.scrollHeight) + 'px';
  }
  function toggleTheme() {
    const currentTheme = appLayout.dataset.theme;
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    appLayout.dataset.theme = newTheme;
    localStorage.setItem('theme', newTheme);
  }
  // --- State & Storage ---
  function loadConversations() {
    const key = `chatConversations_${username}`;
    const stored = localStorage.getItem(key);
    conversations = stored ? JSON.parse(stored) : [];
  }

  function saveConversations() {
    const key = `chatConversations_${username}`;
    localStorage.setItem(key, JSON.stringify(conversations));
  }

  // --- Rendering ---
  function renderSidebar() {
    historyList.innerHTML = '';
    conversations.forEach(chat => {
      const li = document.createElement('li');
      li.dataset.chatId = chat.id;
      li.className = chat.id === activeChatId ? 'active' : '';

      // Title Span
      const titleSpan = document.createElement('span');
      titleSpan.className = 'history-title';
      titleSpan.textContent = chat.title;
      li.appendChild(titleSpan);

      // Actions Div
      const actionsDiv = document.createElement('div');
      actionsDiv.className = 'history-item-actions';

      // Rename Button
      const renameBtn = document.createElement('button');
      renameBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>`;
      renameBtn.title = '重命名';
      renameBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        handleRename(chat.id, li);
      });

      // Delete Button
      const deleteBtn = document.createElement('button');
      deleteBtn.className = 'delete-btn';
      deleteBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>`;
      deleteBtn.title = '删除';
      deleteBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        handleDelete(chat.id);
      });

      actionsDiv.appendChild(renameBtn);
      actionsDiv.appendChild(deleteBtn);
      li.appendChild(actionsDiv);

      li.addEventListener('click', () => setActiveChat(chat.id));
      historyList.appendChild(li);
    });
  }

  function renderChatHistory() {
    chatHistory.innerHTML = '';
    const activeChat = conversations.find(c => c.id === activeChatId);
    if (!activeChat || activeChat.messages.length === 0) {
      appendMessage({ sender: 'bot', text: '你好！今天想做什么菜？\n请输入食材或菜名…' });
    } else {
      activeChat.messages.forEach(appendMessage);
    }
  }

  // --- Action Handlers ---
  function handleRename(chatId, listItem) {
    const titleSpan = listItem.querySelector('.history-title');
    const currentTitle = titleSpan.textContent;

    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentTitle;

    listItem.replaceChild(input, titleSpan);
    input.focus();
    input.select();

    const finishEditing = () => {
      const newTitle = input.value.trim();
      if (newTitle && newTitle !== currentTitle) {
        const chat = conversations.find(c => c.id === chatId);
        chat.title = newTitle;
        saveConversations();
      }
      renderSidebar(); // Re-render to restore the span and show new title
    };

    input.addEventListener('blur', finishEditing);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        finishEditing();
      } else if (e.key === 'Escape') {
        input.value = currentTitle; // Revert
        finishEditing();
      }
    });
  }

  function handleDelete(chatId) {
    if (confirm('确定要删除这个对话吗？此操作无法撤销。')) {
      conversations = conversations.filter(c => c.id !== chatId);
      saveConversations();

      if (activeChatId === chatId) {
        // If the active chat was deleted, switch to another or create a new one
        if (conversations.length > 0) {
          setActiveChat(conversations[0].id);
        } else {
          createNewChat();
        }
      } else {
        renderSidebar(); // Just re-render if a non-active chat was deleted
      }
    }
  }

  // --- Chat Logic ---
  function setActiveChat(chatId) {
    activeChatId = chatId;
    renderSidebar();
    renderChatHistory();
    toggleInput(true);
  }

  function createNewChat() {
    const newChat = {
      id: `chat-${Date.now()}`,
      title: '新的对话',
      messages: []
    };
    conversations.unshift(newChat);
    setActiveChat(newChat.id);
    saveConversations();
  }

  function renderRecipeCard(recipe) {
    const cardWrapper = document.createElement('div');
    cardWrapper.className = 'recipe-card-wrapper';

    const card = document.createElement('div');
    card.className = 'recipe-card';

    // 菜品标题
    const title = document.createElement('h2');
    title.className = 'recipe-title';
    title.textContent = recipe["菜品名称"] || "未命名菜品";

    // 图片（可选）
    if (recipe["菜品图片"]) {
      const image = document.createElement("img");
      image.src = recipe["菜品图片"];
      image.alt = recipe["菜品名称"] || "菜品图片";
      image.className = "recipe-image"; // 确保 style.css 有样式
      card.appendChild(image); // ✅ 直接添加到 card，而不是 front
    }

    // 原材料
    const ingredients = document.createElement('div');
    ingredients.className = 'recipe-section';
    ingredients.innerHTML = `<strong>原材料及用量：</strong><br>` +
      Object.entries(recipe["原材料及用量"] || {})
        .map(([key, val]) => `<span class="tag">${key}: ${val}</span>`).join(' ');

    // 佐料
    const seasonings = document.createElement('div');
    seasonings.className = 'recipe-section';
    seasonings.innerHTML = `<strong>佐料及用量：</strong><br>` +
      Object.entries(recipe["佐料及用量"] || {})
        .map(([key, val]) => `<span class="tag">${key}: ${val}</span>`).join(' ');

    // 做法
    const steps = document.createElement('div');
    steps.className = 'recipe-section';
    steps.innerHTML = `<strong>做法：</strong><ol>` +
      (recipe["做法"] || []).map(step => `<li>${step}</li>`).join('') + `</ol>`;

    // 营养建议
    const nutrition = document.createElement('div');
    nutrition.className = 'recipe-section';
    nutrition.innerHTML = `<strong>营养与搭配建议：</strong><p>${recipe["营养与搭配建议"] || "无"}</p>`;

    // 热量和价格
    const meta = document.createElement('div');
    meta.className = 'recipe-section recipe-meta';
    meta.innerHTML = `
    <span>💰 价格：${recipe["预估总价格"] || "未知"} 元</span>
    <span>🔥 热量：${recipe["预估总热量"] || "未知"} 千卡</span>
  `;
    // 复制按钮
    const copyBtn = document.createElement("button");
    copyBtn.className = "copy-button";
    copyBtn.innerHTML = `📋 复制内容`;
    copyBtn.addEventListener("click", () => {
      const textToCopy = `
【菜品名称】：${recipe["菜品名称"] || "未知"}
【原材料及用量】：
${Object.entries(recipe["原材料及用量"] || {}).map(([k, v]) => `- ${k}：${v}`).join('\n')}
【佐料及用量】：
${Object.entries(recipe["佐料及用量"] || {}).map(([k, v]) => `- ${k}：${v}`).join('\n')}
【做法】：
${(recipe["做法"] || []).map((step, i) => `${i + 1}. ${step}`).join('\n')}
【营养与搭配建议】：
${recipe["营养与搭配建议"] || "无"}
【预估总价格】：${recipe["预估总价格"] || "未知"} 元
【预估总热量】：${recipe["预估总热量"] || "未知"} 千卡
    `.trim();

      navigator.clipboard.writeText(textToCopy).then(() => {
        copyBtn.textContent = "已复制 ✅";
        setTimeout(() => (copyBtn.textContent = "复制内容"), 2000);
      });
    });
    // 重新生成按钮
    const actionWrapper = document.createElement("div");
    actionWrapper.className = "recipe-actions";

    if (recipe.__sourceQuery) {
      const redoBtn = document.createElement("button");
      redoBtn.className = "redo-button";
      redoBtn.innerHTML = "🔄 重新生成";
      redoBtn.addEventListener("click", () => {
        submitInput(recipe.__sourceQuery, true); // true 表示重新生成
      });
      actionWrapper.appendChild(redoBtn);
    }

    actionWrapper.appendChild(copyBtn);




    // 拼接所有内容
    card.appendChild(title);
    card.appendChild(ingredients);
    card.appendChild(seasonings);
    card.appendChild(steps);
    card.appendChild(nutrition);
    card.appendChild(meta);
    card.appendChild(actionWrapper);
    cardWrapper.appendChild(card);
    

    return cardWrapper;
  }

  async function submitInput(queryText = null, isRedo = false) {
    const query = queryText || userInput.value.trim();
    // 简化后的检查：如果只有文本框为空，则不发送
    if (!query) return;

    // 2. 准备用户消息对象（已移除 imageData）
    const userMessage = { 
        sender: 'user', 
        text: query,
    };

    if (!isRedo) {
      addMessageToActiveChat(userMessage);
      appendMessage(userMessage);
    }

    toggleInput(false);

    // 3. 清理输入区（已移除图片相关的清理）
    userInput.value = "";
    userInput.style.height = 'auto';
    

    const activeChat = conversations.find(c => c.id === activeChatId);
    if (activeChat.messages.length === 1 && activeChat.title === '新的对话') {
      activeChat.title = query.length > 20 ? query.substring(0, 20) + '…' : query;
      renderSidebar();
    }

    // 创建AbortController用于取消请求
    currentAbortController = new AbortController();
    // 显示加载动画并将按钮变为终止按钮
    const loadingElement = appendMessage({ sender: 'bot', text: '', isLoading: true });
    currentLoadingElement = loadingElement;
    setSendButtonToAbort(); // 切换为终止按钮

    const contentDiv = loadingElement.querySelector('.message-content');
    contentDiv.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';
    let fullBotResponse = "";

    try {
      // ✅ 修复1 (续): 现在可以安全地使用 userMessage
      const endpoint = "/api/ask";
      const body = JSON.stringify({ 
          query: query, 
          username: username, 
          session_id: activeChatId 
      });
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body,
        signal: currentAbortController.signal
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`HTTP error! status: ${res.status}, message: ${errorText}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      let partialRecipe = {};
      let currentCard = null;

      let partialDishName = ""; // 缓存未完全的菜品名称
      let isMaterialsComplete = false; // 标记“原材料及用量”是否完整解析

      const regex = /【([^【】]+?)】：([\s\S]*?)(?=\n*【[^】]+?】：|---END_OF_DISH---|$)/g;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        let match;
        while ((match = regex.exec(buffer)) !== null) {
          const label = match[1].trim(); // 字段名称
          const val = match[2].trim(); // 字段内容


          if (label === "菜品名称") {
            // 如果菜品名称是第一次出现，缓存菜品名称
            if (!partialDishName && isMaterialsComplete) {
              partialDishName = val.split("【")[0].trim(); // 确保去除后续的【字符
              partialRecipe.__sourceQuery = query;
              partialRecipe["菜品名称"] = partialDishName;
              currentCard = renderRecipeCard(partialRecipe);
              contentDiv.appendChild(currentCard);
            }
          }

          // 累积更新其他字段
          switch (label) {
            case "原材料及用量":
              partialRecipe["原材料及用量"] = parseList(val);
              isMaterialsComplete = true;  // 一旦“原材料及用量”完整，允许菜品名称渲染
              break;
            case "佐料及用量":
              partialRecipe["佐料及用量"] = parseList(val);
              break;
            case "做法":
              partialRecipe["做法"] = parseSteps(val);
              break;
            case "营养与搭配建议":
              partialRecipe["营养与搭配建议"] = val;
              break;
            case "预估总价格":
              partialRecipe["预估总价格"] = parseFloat(val.replace(/[^\d.]/g, "")) || 0;
              break;
            case "预估总热量":
              partialRecipe["预估总热量"] = parseFloat(val.replace(/[^\d.]/g, "")) || 0;
              break;
            case "菜品图片":
              partialRecipe["菜品图片"] = val;
              break;
          }

          if (currentCard && partialRecipe["菜品名称"]) {
            const updatedCard = renderRecipeCard(partialRecipe);
            contentDiv.replaceChild(updatedCard, currentCard);
            currentCard = updatedCard;
          }
        }

        // 完成解析当前菜品后的清理
        while (buffer.includes('---END_OF_DISH---')) {
          addMessageToActiveChat({
            sender: 'bot',
            text: '[结构化菜谱已展示为卡片]',
            structured: true,
            recipe: partialRecipe
          });

          buffer = buffer.slice(buffer.indexOf('---END_OF_DISH---') + 17);
          partialRecipe = {};  // 清空当前菜品的内容
          currentCard = null;

          // 清空菜品名称缓存
          partialDishName = "";
          isMaterialsComplete = false; // 重置原材料标志
        }

        scrollToBottom();
      }

      // 最后可能还有一部分未结束的内容
      if (partialRecipe["菜品名称"]) {
        addMessageToActiveChat({
          sender: 'bot',
          text: '[结构化菜谱已展示为卡片]',
          structured: true,
          recipe: partialRecipe
        });
      }

    } catch (err) {
      if (err.name === 'AbortError') {
        // 用户主动终止的处理
        const contentDiv = currentLoadingElement.querySelector('.message-content');
        const truncatedResponse = fullBotResponse || "思考已终止";
        contentDiv.innerHTML = marked.parse(truncatedResponse + "<br><em>（用户终止了思考过程）</em>");
        addMessageToActiveChat({ sender: 'bot', text: truncatedResponse });
      } else {
        console.error("请求或处理流时发生错误:", err);
        const errorText = `🚫 请求出错: ${err.message}`;
         if (currentLoadingElement) {
            const contentDiv = currentLoadingElement.querySelector('.message-content');
            if(contentDiv) {
                contentDiv.innerHTML = marked.parse(errorText);
            }
        }
        addMessageToActiveChat({ sender: 'bot', text: errorText });
      }
    } finally {
      currentAbortController = null;
      currentLoadingElement = null;
      saveConversations();
      resetSendButton();// 恢复发送按钮
      toggleInput(true);
      scrollToBottom();
    }
  }
// ============== 终止功能相关函数（三个） ==============
  function setSendButtonToAbort() {
    sendButton.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
        <rect x="6" y="6" width="12" height="12" rx="1"/>
      </svg>
    `;
    sendButton.title = "终止思考";
    sendButton.disabled = false; // 确保按钮启用
    sendButton.classList.add('aborting');
    sendButton.removeEventListener('click', submitInput);
    sendButton.addEventListener('click', abortThinking);
  }

  function resetSendButton() {
    sendButton.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2 .01 7z"/>
      </svg>
    `;
    sendButton.title = "发送消息";
    sendButton.disabled = false; // 确保按钮启用
    sendButton.classList.remove('aborting');
    sendButton.removeEventListener('click', abortThinking);
    sendButton.addEventListener('click', () => submitInput());
  }

  function abortThinking() {
    if (currentAbortController) {
      // 1. 取消前端请求
      currentAbortController.abort();
      
      // 2. 通知后端终止处理
      fetch("http://localhost:8000/api/terminate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          username: username,
          session_id: activeChatId
        })
      }).catch(console.error);
      if (currentLoadingElement) {
        const contentDiv = currentLoadingElement.querySelector('.message-content');
        contentDiv.innerHTML = marked.parse("思考已终止");
      }
      resetSendButton();
    }
  }
  // 原材料 / 佐料：从文本解析为对象
  function parseList(raw) {
    const lines = raw.split('\n');
    const obj = {};
    for (const line of lines) {
      const [key, val] = line.replace(/^- /, '').split('：');
      if (key && val) obj[key.trim()] = val.trim();
    }
    return obj;
  }

  // 做法：解析为步骤数组
  function parseSteps(raw) {
    return raw
      .split('\n')
      .map(line => line.replace(/^\d+\.\s*/, '').trim())
      .filter(Boolean);
  }


  function addMessageToActiveChat(message) {
    const activeChat = conversations.find(c => c.id === activeChatId);
    if (activeChat) {
      activeChat.messages.push(message);
    }
  }

  // --- DOM Manipulation (mostly unchanged) ---
   function appendMessage({ sender, text, isLoading = false }) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${sender}-message`;
    
    // 保留用户消息的“复制”按钮功能
    if (sender === 'user') {
      const copyBtn = document.createElement('button');
      copyBtn.className = 'copy-btn';
      copyBtn.title = '复制内容';
      const copyIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;
      const checkIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
      copyBtn.innerHTML = copyIcon;
      copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(text).then(() => {
          copyBtn.innerHTML = checkIcon;
          copyBtn.title = '已复制!';
          setTimeout(() => {
            copyBtn.innerHTML = copyIcon;
            copyBtn.title = '复制内容';
          }, 1500);
        }).catch(err => { console.error('无法复制文本: ', err); });
      });
      msgDiv.appendChild(copyBtn);
    }

    // 创建头像元素
    const avatarDiv = document.createElement('div');
    avatarDiv.className = `avatar ${sender}-avatar`;
    if (sender === 'user') {
      // 用户头像固定为默认SVG图标
      avatarDiv.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" class="user-default-icon">
          <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
        </svg>
      `;
    } else { // sender === 'bot'
      // AI 助手头像固定为本地图片
      const botAvatarUrl = '/assets/bot-avatar.png';
      avatarDiv.innerHTML = `<img src="${botAvatarUrl}" alt="食悟美食助手">`;
    }

    // 创建消息内容元素
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // 将头像添加到消息容器中
    msgDiv.appendChild(avatarDiv);

    if (isLoading) {
      contentDiv.innerHTML = `<div class="loading-dots"><span></span><span></span><span></span></div>`;
    } else {
      // 关键修改：不再检查 imageData，只处理文本
      let contentToRender = '';
      if (typeof text === 'string') {
        contentToRender = text;
      } else {
        console.warn('警告: appendMessage 函数收到了一个非字符串的 "text" 属性。值为:', text);
        contentToRender = "```json\n" + JSON.stringify(text, null, 2) + "\n```"; 
      }
      contentDiv.innerHTML = marked.parse(contentToRender);
    }

    msgDiv.appendChild(contentDiv);
    chatHistory.appendChild(msgDiv);
    scrollToBottom();
    return msgDiv;
  }

  function toggleInput(enabled) {
    userInput.disabled = !enabled;
    sendButton.disabled = !enabled;
    if (enabled) userInput.focus();
  }

  function scrollToBottom() {
    chatHistory.scrollTop = chatHistory.scrollHeight;
  }
  async function fetchAndDisplayRecommendation() {
    const listElement = document.getElementById('recommendation-list');
    if (!listElement) return;

    listElement.innerHTML = `<li class="loading-text">正在为您获取今日灵感...</li>`;

    try {
      const response = await fetch('http://localhost:8000/api/daily-recommendation');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const recipe = await response.json();

      // ... (做法解析逻辑保持不变)
      const recipeName = recipe.菜谱名称 || '暂无';
      const recipeFlavor = recipe.特性 || '暂无';
      const ingredientsHtml = recipe.原料 || '暂无';
      const seasoningsHtml = recipe.调料 || '暂无';
      let stepsArray = [];
      const stepsText = recipe.做法 || '';
      if (stepsText.trim()) {
        const stepMarkerRegex = /(?=\(\d+\)|^\d+、|^\d+\.|\s\d+\.)/;
        if (stepMarkerRegex.test(stepsText)) {
          stepsArray = stepsText.split(stepMarkerRegex).map(s => s.trim()).filter(s => s);
        } else {
          stepsArray = stepsText.split(/[\r\n]+/).map(s => s.trim()).filter(s => s);
        }
        if (stepsArray.length === 0 && stepsText.trim()) {
          stepsArray.push(stepsText.trim());
        }
      }
      const stepsHtml = stepsArray.length > 0
        ? stepsArray.map(step => `<li>${step}</li>`).join('')
        : '<li>暂无详细步骤</li>';

      listElement.innerHTML = ''; // 清空加载状态
      const recipeCard = document.createElement('li');

      // ✅ 关键改动：构建包含图片的 HTML
      // 检查 recipe.imageUrl 是否存在且不为空
      const imageHtml = recipe.imageUrl
        ? `<img src="${recipe.imageUrl}" alt="${recipeName}" style="width:100%; border-radius: 8px; margin-bottom: 12px;">`
        : '';

      recipeCard.innerHTML = `
      ${imageHtml} 
      <h4>${recipeName}</h4>
      <p><strong>特性:</strong> ${recipeFlavor}</p>
      <p><strong>原料:</strong> ${ingredientsHtml}</p>
      <p><strong>调料:</strong> ${seasoningsHtml}</p>
      <p><strong>做法:</strong></p>
      <ol style="padding-left: 20px;">${stepsHtml}</ol>
    `;

      listElement.appendChild(recipeCard);

    } catch (error) {
      console.error("获取每日推荐失败:", error);
      listElement.innerHTML = `<li class="loading-text">哎呀，获取推荐失败了！<br>请检查浏览器控制台以获取错误详情。</li>`;
    }
  }

  // --- 新增：用户信息逻辑 ---
  function initUserInfo() {
    // 更新按钮文本
    if (username) {
      const btnText = userInfoBtn.querySelector('.btn-text');
      if (btnText) {
        btnText.textContent = `欢迎，${username}`;
      }
      userIdDisplay.value = `用户ID: ${username}`;
    }

    // // 更新用户ID显示
    // if (userData.id) {
    //   userIdDisplay.value = `用户ID: ${userData.id}`;
    // }
  }

  function toggleUserDetails() {
    userDetails.classList.toggle('active');
  }

  // 修改密码按钮点击事件
  function handleChangePassword() {
    changePasswordForm.style.display = 'block';
  }

  // 取消密码修改
  function cancelPasswordChange() {
    changePasswordForm.style.display = 'none';
    // 清空输入框
    oldPasswordInput.value = '';
    newPasswordInput.value = '';
    confirmPasswordInput.value = '';
  }

  // 处理密码修改
  async function handlePasswordChange() {
    const oldPassword = oldPasswordInput.value.trim();
    const newPassword = newPasswordInput.value.trim();
    const confirmPassword = confirmPasswordInput.value.trim();

    if (!oldPassword || !newPassword || !confirmPassword) {
      alert('请填写所有字段');
      return;
    }

    if (newPassword !== confirmPassword) {
      alert('新密码与确认密码不一致');
      return;
    }

    // if (newPassword.length < 6) {
    //   alert('密码长度至少为6位');
    //   return;
    // }

    try {
      const res = await fetch('http://localhost:8000/api/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, oldPassword, newPassword })
      });

      const data = await res.json();
      if (data.success) {
        alert('密码修改成功！');
        cancelPasswordChange();
      } else {
        alert('密码修改失败: ' + (data.message || '未知错误'));
      }
    } catch (err) {
      console.error('密码修改请求错误:', err);
      alert('服务器错误，请稍后重试');
    }
  }

  // 退出登录函数
  function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('username');
    window.location.href = 'index.html';
  }
  // Start the application
  init();
});