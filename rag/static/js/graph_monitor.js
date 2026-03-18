// Graph 节点定义 - 根据实际的 graph_rag2.png 布局
const graphNodes = {
    '__start__': { x: 400, y: 50, label: 'START', icon: '🚀' },
    'websearch': { x: 200, y: 200, label: 'Web搜索', icon: '🌐' },
    'retriever': { x: 600, y: 200, label: '向量检索', icon: '📚' },
    'grade_documents': { x: 600, y: 350, label: '文档评分', icon: '⭐' },
    'transform_query': { x: 600, y: 500, label: '查询转换', icon: '🔄' },
    'generate': { x: 400, y: 650, label: '生成回答', icon: '✨' },
    '__end__': { x: 400, y: 800, label: 'END', icon: '🎯' }
};

// Graph 边定义 - 根据实际流程
const graphEdges = [
    { from: '__start__', to: 'websearch', label: 'web', condition: true },
    { from: '__start__', to: 'retriever', label: 'rag', condition: true },
    { from: 'websearch', to: 'generate' },
    { from: 'retriever', to: 'grade_documents' },
    { from: 'grade_documents', to: 'generate', label: '相关' },
    { from: 'grade_documents', to: 'transform_query', label: '不相关' },
    { from: 'grade_documents', to: 'websearch', label: '转web' },
    { from: 'transform_query', to: 'retriever' },
    { from: 'generate', to: '__end__', label: '完成' },
    { from: 'generate', to: 'transform_query', label: '重试' },
    { from: 'generate', to: 'generate', label: '幻觉重试' }
];

let currentExecution = {
    nodes: {},
    timeline: [],
    startTime: null,
    previousNode: null,
    executionPath: []
};

let eventSource = null;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initGraph();
    addBotMessage('你好！我是 RAG Agent 智能助手。提问后，你可以在右侧看到实时的执行流程。');
});

// 初始化 SVG
function initGraph() {
    const svg = document.getElementById('graphSvg');
    const ns = 'http://www.w3.org/2000/svg';
    svg.setAttribute('height', '850');

    // 添加箭头标记
    const defs = document.createElementNS(ns, 'defs');

    // 普通箭头
    const marker = document.createElementNS(ns, 'marker');
    marker.setAttribute('id', 'arrowhead');
    marker.setAttribute('markerWidth', '10');
    marker.setAttribute('markerHeight', '10');
    marker.setAttribute('refX', '9');
    marker.setAttribute('refY', '3');
    marker.setAttribute('orient', 'auto');
    const polygon = document.createElementNS(ns, 'polygon');
    polygon.setAttribute('points', '0 0, 10 3, 0 6');
    polygon.setAttribute('fill', '#475569');
    marker.appendChild(polygon);
    defs.appendChild(marker);

    // 激活状态箭头
    const markerActive = document.createElementNS(ns, 'marker');
    markerActive.setAttribute('id', 'arrowhead-active');
    markerActive.setAttribute('markerWidth', '10');
    markerActive.setAttribute('markerHeight', '10');
    markerActive.setAttribute('refX', '9');
    markerActive.setAttribute('refY', '3');
    markerActive.setAttribute('orient', 'auto');
    const polygonActive = document.createElementNS(ns, 'polygon');
    polygonActive.setAttribute('points', '0 0, 10 3, 0 6');
    polygonActive.setAttribute('fill', '#fbbf24');
    markerActive.appendChild(polygonActive);
    defs.appendChild(markerActive);

    svg.appendChild(defs);

    // 绘制边
    graphEdges.forEach((edge, index) => {
        const fromNode = graphNodes[edge.from];
        const toNode = graphNodes[edge.to];

        if (!fromNode || !toNode) return;

        const g = document.createElementNS(ns, 'g');
        g.setAttribute('class', 'edge-group');
        g.setAttribute('data-from', edge.from);
        g.setAttribute('data-to', edge.to);

        // 计算路径
        let pathD;
        if (edge.from === edge.to) {
            // 自循环
            pathD = `M ${fromNode.x + 70} ${fromNode.y}
                     C ${fromNode.x + 120} ${fromNode.y - 40},
                       ${fromNode.x + 120} ${fromNode.y + 40},
                       ${fromNode.x + 70} ${fromNode.y}`;
        } else if (edge.from === 'transform_query' && edge.to === 'retriever') {
            // transform_query 到 retriever：从右侧绕过的曲线
            pathD = `M ${fromNode.x} ${fromNode.y - 30}
                     C ${fromNode.x + 100} ${fromNode.y - 100},
                       ${toNode.x + 100} ${toNode.y + 100},
                       ${toNode.x} ${toNode.y + 30}`;
        } else if (edge.from === 'retriever' && edge.to === 'grade_documents') {
            // retriever 到 grade_documents：垂直向下的直线
            pathD = `M ${fromNode.x} ${fromNode.y + 30}
                     L ${toNode.x} ${toNode.y - 30}`;
        } else {
            const dx = toNode.x - fromNode.x;
            const dy = toNode.y - fromNode.y;

            // 如果是垂直方向（x坐标相同）
            if (dx === 0) {
                // 直线
                pathD = `M ${fromNode.x} ${fromNode.y + 30}
                         L ${toNode.x} ${toNode.y - 30}`;
            } else {
                // 曲线连接
                const offsetX = dx > 0 ? 70 : -70;
                const offsetY = dy > 0 ? 30 : -30;

                pathD = `M ${fromNode.x + offsetX} ${fromNode.y + (dy > 0 ? 30 : -30)}
                         Q ${(fromNode.x + toNode.x) / 2} ${(fromNode.y + toNode.y) / 2}
                           ${toNode.x - offsetX} ${toNode.y - offsetY}`;
            }
        }

        const path = document.createElementNS(ns, 'path');
        path.setAttribute('d', pathD);
        path.setAttribute('class', 'edge');
        path.setAttribute('stroke-dasharray', '0');
        g.appendChild(path);

        // 添加流动的粒子效果
        const particle = document.createElementNS(ns, 'circle');
        particle.setAttribute('r', '4');
        particle.setAttribute('class', 'edge-particle');
        particle.setAttribute('fill', '#fbbf24');
        particle.style.display = 'none';

        const animateMotion = document.createElementNS(ns, 'animateMotion');
        animateMotion.setAttribute('dur', '1.5s');
        animateMotion.setAttribute('repeatCount', 'indefinite');
        const mpath = document.createElementNS(ns, 'mpath');
        mpath.setAttributeNS('http://www.w3.org/1999/xlink', 'xlink:href', `#edge-path-${index}`);
        animateMotion.appendChild(mpath);
        particle.appendChild(animateMotion);

        path.setAttribute('id', `edge-path-${index}`);
        g.appendChild(particle);

        // 边标签
        if (edge.label) {
            const text = document.createElementNS(ns, 'text');
            const midX = edge.from === edge.to ? fromNode.x + 130 : (fromNode.x + toNode.x) / 2;
            const midY = edge.from === edge.to ? fromNode.y : (fromNode.y + toNode.y) / 2;
            text.setAttribute('x', midX);
            text.setAttribute('y', midY - 5);
            text.setAttribute('fill', '#64748b');
            text.setAttribute('font-size', '11');
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('class', 'edge-label');
            text.textContent = edge.label;
            g.appendChild(text);
        }

        svg.appendChild(g);
    });

    // 绘制节点
    Object.entries(graphNodes).forEach(([id, node]) => {
        const g = document.createElementNS(ns, 'g');
        g.setAttribute('class', 'node');
        g.setAttribute('data-node', id);
        g.onclick = () => showNodeDetails(id);

        const rect = document.createElementNS(ns, 'rect');
        rect.setAttribute('class', 'node-rect');
        rect.setAttribute('x', node.x - 70);
        rect.setAttribute('y', node.y - 30);
        rect.setAttribute('width', '140');
        rect.setAttribute('height', '60');
        g.appendChild(rect);

        const icon = document.createElementNS(ns, 'text');
        icon.setAttribute('class', 'node-icon');
        icon.setAttribute('x', node.x);
        icon.setAttribute('y', node.y - 5);
        icon.setAttribute('text-anchor', 'middle');
        icon.textContent = node.icon;
        g.appendChild(icon);

        const text = document.createElementNS(ns, 'text');
        text.setAttribute('class', 'node-text');
        text.setAttribute('x', node.x);
        text.setAttribute('y', node.y + 18);
        text.setAttribute('text-anchor', 'middle');
        text.textContent = node.label;
        g.appendChild(text);

        svg.appendChild(g);
    });
}

// 更新节点状态
function updateNodeStatus(nodeId, status, data = {}) {
    // 清除所有节点的高亮状态
    document.querySelectorAll('.node').forEach(node => {
        node.classList.remove('active', 'completed', 'error');
    });

    // 清除所有边的激活状态
    document.querySelectorAll('.edge-group').forEach(edge => {
        edge.classList.remove('active');
        const particle = edge.querySelector('.edge-particle');
        if (particle) particle.style.display = 'none';
    });

    // 只高亮当前节点
    const node = document.querySelector(`[data-node="${nodeId}"]`);
    if (node && status === 'active') {
        node.classList.add('active');
    }

    // 激活从上一个节点到当前节点的边
    if (currentExecution.previousNode && status === 'active') {
        activateEdge(currentExecution.previousNode, nodeId);
        currentExecution.executionPath.push({ from: currentExecution.previousNode, to: nodeId });
    }

    // 更新执行数据
    currentExecution.nodes[nodeId] = {
        status,
        data,
        timestamp: new Date().toISOString()
    };

    // 添加到时间线
    if (status === 'active') {
        addTimelineItem(nodeId, status);
    }

    // 更新前一个节点
    if (status === 'active') {
        currentExecution.previousNode = nodeId;
    }
}

// 激活边 - 显示数据流动
function activateEdge(fromNode, toNode) {
    const edgeGroup = document.querySelector(`.edge-group[data-from="${fromNode}"][data-to="${toNode}"]`);
    if (edgeGroup) {
        const path = edgeGroup.querySelector('.edge');
        const particle = edgeGroup.querySelector('.edge-particle');
        const label = edgeGroup.querySelector('.edge-label');

        // 激活边
        path.classList.add('active');
        path.setAttribute('marker-end', 'url(#arrowhead-active)');

        // 显示流动粒子
        if (particle) {
            particle.style.display = 'block';
        }

        // 高亮标签
        if (label) {
            label.setAttribute('fill', '#fbbf24');
            label.setAttribute('font-weight', 'bold');
        }

        // 1.5秒后恢复
        setTimeout(() => {
            path.classList.remove('active');
            path.setAttribute('marker-end', 'url(#arrowhead)');
            if (particle) {
                particle.style.display = 'none';
            }
            if (label) {
                label.setAttribute('fill', '#64748b');
                label.setAttribute('font-weight', 'normal');
            }
        }, 1500);
    }
}

// 添加时间线项
function addTimelineItem(nodeId, status) {
    const timeline = document.getElementById('timeline');
    const node = graphNodes[nodeId];

    if (!node) return;

    const item = document.createElement('div');
    item.className = `timeline-item ${status}`;

    const elapsed = currentExecution.startTime
        ? ((Date.now() - currentExecution.startTime) / 1000).toFixed(2)
        : '0.00';

    item.innerHTML = `
        <div class="timeline-icon">${node.icon}</div>
        <div class="timeline-content">
            <div class="timeline-node">${node.label}</div>
            <div class="timeline-time">+${elapsed}s</div>
        </div>
    `;

    timeline.insertBefore(item, timeline.firstChild);
}

// 显示节点详情
function showNodeDetails(nodeId) {
    const details = document.getElementById('nodeDetails');
    const nodeData = currentExecution.nodes[nodeId];
    const node = graphNodes[nodeId];

    if (!node) return;

    if (!nodeData) {
        details.innerHTML = `
            <h4>${node.icon} ${node.label}</h4>
            <p class="placeholder">该节点尚未执行</p>
        `;
        return;
    }

    let dataHtml = '<div class="data-grid">';

    if (nodeData.data.question) {
        dataHtml += `<div class="data-item"><strong>问题:</strong> ${escapeHtml(nodeData.data.question)}</div>`;
    }

    if (nodeData.data.documents_count !== undefined) {
        dataHtml += `<div class="data-item"><strong>文档数:</strong> ${nodeData.data.documents_count}</div>`;
    }

    if (nodeData.data.transform_count !== undefined) {
        dataHtml += `<div class="data-item"><strong>转换次数:</strong> ${nodeData.data.transform_count}</div>`;
    }

    if (nodeData.data.generation) {
        const genText = escapeHtml(nodeData.data.generation);
        const preview = genText.length > 200 ? genText.substring(0, 200) + '...' : genText;
        dataHtml += `<div class="data-item"><strong>生成内容:</strong> ${preview}</div>`;
    }

    dataHtml += '</div>';

    details.innerHTML = `
        <h4>${node.icon} ${node.label}</h4>
        <div class="status-indicator status-${nodeData.status}">${nodeData.status === 'completed' ? '已完成' : '执行中'}</div>
        ${dataHtml}
        <div class="timestamp">执行时间: ${new Date(nodeData.timestamp).toLocaleTimeString()}</div>
    `;
}

// 发送消息
async function sendMessage() {
    const questionInput = document.getElementById('questionInput');
    const question = questionInput.value.trim();

    if (!question) return;

    // 添加用户消息
    addUserMessage(question);
    questionInput.value = '';

    // 重置状态
    resetExecution();
    setLoading(true);
    updateStatus('running');

    // 激活 START 节点
    updateNodeStatus('__start__', 'active');
    await sleep(500);

    try {
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const jsonStr = line.substring(6).trim();
                    if (!jsonStr) continue;

                    try {
                        const data = JSON.parse(jsonStr);

                        switch (data.type) {
                            case 'start':
                                currentExecution.startTime = Date.now();
                                break;

                            case 'node':
                                // 只激活当前节点，不保持completed状态
                                updateNodeStatus(data.node, 'active', data.data);
                                break;

                            case 'end':
                                updateNodeStatus('__end__', 'active');
                                await sleep(300);
                                addBotMessage(data.answer);
                                updateStatus('completed');
                                setLoading(false);
                                // 清除所有高亮
                                document.querySelectorAll('.node').forEach(node => {
                                    node.classList.remove('active');
                                });
                                document.querySelectorAll('.edge-group').forEach(edge => {
                                    edge.classList.remove('active');
                                    const particle = edge.querySelector('.edge-particle');
                                    if (particle) particle.style.display = 'none';
                                });
                                break;

                            case 'error':
                                addErrorMessage(data.error);
                                updateStatus('error');
                                setLoading(false);
                                break;
                        }
                    } catch (e) {
                        console.error('解析JSON失败:', e, jsonStr);
                    }
                }
            }
        }

    } catch (error) {
        console.error('Error:', error);
        addErrorMessage('请求失败: ' + error.message);
        updateStatus('error');
        setLoading(false);
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 重置执行状态
function resetExecution() {
    currentExecution = {
        nodes: {},
        timeline: [],
        startTime: null,
        previousNode: '__start__',
        executionPath: []
    };

    // 清空时间线
    document.getElementById('timeline').innerHTML = '';
    document.getElementById('nodeDetails').innerHTML = '<p class="placeholder">点击节点查看详细信息</p>';

    // 重置所有节点状态
    document.querySelectorAll('.node').forEach(node => {
        node.classList.remove('active', 'completed', 'error');
    });

    // 重置所有边
    document.querySelectorAll('.edge').forEach(edge => {
        edge.classList.remove('active');
        edge.setAttribute('marker-end', 'url(#arrowhead)');
    });

    document.querySelectorAll('.edge-particle').forEach(p => {
        p.style.display = 'none';
    });
}

// 更新状态徽章
function updateStatus(status) {
    const badge = document.getElementById('statusBadge');
    badge.className = 'status-badge';

    switch (status) {
        case 'running':
            badge.classList.add('running');
            badge.textContent = '执行中';
            break;
        case 'completed':
            badge.classList.add('completed');
            badge.textContent = '已完成';
            break;
        case 'error':
            badge.classList.add('error');
            badge.textContent = '错误';
            break;
        default:
            badge.textContent = '就绪';
    }
}

// 聊天相关函数
function addUserMessage(text) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-user';
    messageDiv.innerHTML = `<div class="message-content">${escapeHtml(text)}</div>`;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addBotMessage(text) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-bot';
    messageDiv.innerHTML = `<div class="message-content">${escapeHtml(text)}</div>`;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addErrorMessage(text) {
    const chatMessages = document.getElementById('chatMessages');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'message message-bot';
    errorDiv.innerHTML = `<div class="message-content" style="background: #fee; color: #c33; border-color: #c33;">❌ ${escapeHtml(text)}</div>`;
    chatMessages.appendChild(errorDiv);
    scrollToBottom();
}

function setLoading(isLoading) {
    const sendBtn = document.getElementById('sendBtn');
    const questionInput = document.getElementById('questionInput');
    const btnText = document.getElementById('btnText');
    const btnLoader = document.getElementById('btnLoader');

    sendBtn.disabled = isLoading;
    questionInput.disabled = isLoading;

    if (isLoading) {
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline-block';
    } else {
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
}

function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}

// 回车发送
document.addEventListener('DOMContentLoaded', () => {
    const questionInput = document.getElementById('questionInput');
    if (questionInput) {
        questionInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
});
