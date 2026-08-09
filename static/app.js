// 银行内网网络配置生成器 - 前端逻辑

let currentStep = 1;
let analysisData = null;
let devicesConfig = [];

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    showStep(1);
});

// 显示指定步骤
function showStep(step) {
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    document.getElementById(`step${step}`).classList.add('active');
    currentStep = step;
}

// 返回上一步
function backToStep(step) {
    showStep(step);
}

// Step 1 -> Step 2: 路径分析
async function analyzePath() {
    const srcIp = document.getElementById('src_ip').value.trim();
    const dstIp = document.getElementById('dst_ip').value.trim();
    const port = document.getElementById('port').value.trim();
    const protocol = document.getElementById('protocol').value;
    const description = document.getElementById('description').value.trim();

    if (!srcIp || !dstIp) {
        alert('请输入源地址和目的地址');
        return;
    }

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                src_ip: srcIp,
                dst_ip: dstIp,
                port: port,
                protocol: protocol,
                description: description
            })
        });

        const data = await response.json();

        if (data.success) {
            analysisData = data;
            displayAnalysisResult(data);
            showStep(2);
        } else {
            alert('分析失败：' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('请求失败，请检查网络连接');
    }
}

// 显示分析结果
function displayAnalysisResult(data) {
    // 源地址信息
    const srcHtml = `
        <p><strong>输入：</strong>${data.src_parsed.input}</p>
        <p><strong>区域：</strong>${data.src_parsed.zones.join(', ')}</p>
        <p><strong>详情：</strong>${data.src_parsed.detail || '无'}</p>
        <p><strong>IP 数量：</strong>${data.src_parsed.ip_count}</p>
    `;
    document.getElementById('src_result').innerHTML = srcHtml;

    // 目的地址信息
    const dstHtml = `
        <p><strong>输入：</strong>${data.dst_parsed.input}</p>
        <p><strong>区域：</strong>${data.dst_parsed.zones.join(', ')}</p>
        <p><strong>详情：</strong>${data.dst_parsed.detail || '无'}</p>
        <p><strong>IP 数量：</strong>${data.dst_parsed.ip_count}</p>
    `;
    document.getElementById('dst_result').innerHTML = dstHtml;

    // 场景分析
    const sceneHtml = `
        <p><strong>场景类型：</strong>${data.scene_type || '未知'}</p>
        <p><strong>场景描述：</strong>${data.scene_description || '无'}</p>
        <p><strong>管控级别：</strong>${data.control_level || '未知'}</p>
        ${data.policy_info ? `<p><strong>策略要求：</strong>${JSON.stringify(data.policy_info)}</p>` : ''}
    `;
    document.getElementById('scene_result').innerHTML = sceneHtml;
}

// Step 2 -> Step 3: 显示设备配置
function showDeviceConfig() {
    if (!analysisData) {
        alert('请先完成路径分析');
        return;
    }

    const devicesList = document.getElementById('devices_list');
    const devices = analysisData.devices || [];

    if (devices.length === 0) {
        devicesList.innerHTML = '<p>未找到需要配置的设备</p>';
        showStep(4);
        return;
    }

    let html = '';
    devices.forEach((device, index) => {
        html += `
            <div class="device-card">
                <h4>
                    <span class="device-icon">🖥️</span>
                    ${device.name} (${device.type})
                </h4>
                <div class="config-mode">
                    <div>
                        <label>源地址模式：</label>
                        <select id="src_mode_${index}" onchange="toggleModeInputs(${index}, 'src')">
                            <option value="detail">明细地址</option>
                            <option value="addrset">地址集（新建）</option>
                            <option value="existing">引用现有地址集</option>
                        </select>
                    </div>
                    <div id="src_detail_inputs_${index}" class="mode-inputs">
                        <small>将使用上方输入的明细 IP 地址</small>
                    </div>
                    <div id="src_addrset_inputs_${index}" class="mode-inputs" style="display:none;">
                        <label>源地址集名称：</label>
                        <input type="text" id="src_addrset_${index}" placeholder="例如：ADDR_SET_SRC_业务名">
                    </div>
                    <div id="src_existing_inputs_${index}" class="mode-inputs" style="display:none;">
                        <label>现有源地址集名称：</label>
                        <input type="text" id="src_existing_${index}" placeholder="选择已有的地址集名称">
                    </div>
                </div>
                <div class="config-mode">
                    <div>
                        <label>目的地址模式：</label>
                        <select id="dst_mode_${index}" onchange="toggleModeInputs(${index}, 'dst')">
                            <option value="detail">明细地址</option>
                            <option value="addrset">地址集（新建）</option>
                            <option value="existing">引用现有地址集</option>
                        </select>
                    </div>
                    <div id="dst_detail_inputs_${index}" class="mode-inputs">
                        <small>将使用上方输入的明细 IP 地址</small>
                    </div>
                    <div id="dst_addrset_inputs_${index}" class="mode-inputs" style="display:none;">
                        <label>目的地址集名称：</label>
                        <input type="text" id="dst_addrset_${index}" placeholder="例如：ADDR_SET_DST_业务名">
                    </div>
                    <div id="dst_existing_inputs_${index}" class="mode-inputs" style="display:none;">
                        <label>现有目的地址集名称：</label>
                        <input type="text" id="dst_existing_${index}" placeholder="选择已有的地址集名称">
                    </div>
                </div>
                <div class="config-mode">
                    <div>
                        <label>端口模式：</label>
                        <select id="port_mode_${index}" onchange="toggleModeInputs(${index}, 'port')">
                            <option value="detail">明细端口</option>
                            <option value="svcset">服务集（新建）</option>
                            <option value="existing">引用现有服务集</option>
                        </select>
                    </div>
                    <div id="port_detail_inputs_${index}" class="mode-inputs">
                        <small>将使用上方输入的明细端口</small>
                    </div>
                    <div id="port_svcset_inputs_${index}" class="mode-inputs" style="display:none;">
                        <label>服务集名称：</label>
                        <input type="text" id="port_svcset_${index}" placeholder="例如：SVC_SET_业务名">
                    </div>
                    <div id="port_existing_inputs_${index}" class="mode-inputs" style="display:none;">
                        <label>现有服务集名称：</label>
                        <input type="text" id="port_existing_${index}" placeholder="选择已有的服务集名称">
                    </div>
                </div>
            </div>
        `;
    });

    devicesList.innerHTML = html;
    showStep(3);
}

// 切换模式时显示/隐藏对应输入框
function toggleModeInputs(index, type) {
    const modeSelect = document.getElementById(`${type}_mode_${index}`);
    const mode = modeSelect.value;
    
    // 隐藏所有输入框
    document.getElementById(`${type}_detail_inputs_${index}`).style.display = 'none';
    document.getElementById(`${type}_addrset_inputs_${index}`).style.display = 'none';
    document.getElementById(`${type}_existing_inputs_${index}`).style.display = 'none';
    document.getElementById(`${type}_svcset_inputs_${index}`).style.display = 'none';
    
    // 显示对应输入框
    if (mode === 'detail') {
        document.getElementById(`${type}_detail_inputs_${index}`).style.display = 'block';
    } else if (mode === 'addrset') {
        document.getElementById(`${type}_addrset_inputs_${index}`).style.display = 'block';
    } else if (mode === 'existing') {
        document.getElementById(`${type}_existing_inputs_${index}`).style.display = 'block';
    } else if (mode === 'svcset') {
        document.getElementById(`${type}_svcset_inputs_${index}`).style.display = 'block';
    }
}

// Step 3 -> Step 4: 生成配置
async function generateConfig() {
    if (!analysisData) {
        alert('没有分析数据');
        return;
    }

    const devices = analysisData.devices || [];
    if (devices.length === 0) {
        document.getElementById('config_results').innerHTML = '<p>无需生成配置</p>';
        showStep(4);
        return;
    }

    const devicesConfig = [];
    devices.forEach((device, index) => {
        const srcMode = document.getElementById(`src_mode_${index}`).value;
        const dstMode = document.getElementById(`dst_mode_${index}`).value;
        const portMode = document.getElementById(`port_mode_${index}`).value;
        
        devicesConfig.push({
            device: device,
            src_mode: srcMode,
            dst_mode: dstMode,
            port_mode: portMode,
            // 根据模式获取对应的值
            src_addrset_name: srcMode === 'addrset' ? (document.getElementById(`src_addrset_${index}`)?.value || '') : '',
            dst_addrset_name: dstMode === 'addrset' ? (document.getElementById(`dst_addrset_${index}`)?.value || '') : '',
            port_svcset_name: portMode === 'svcset' ? (document.getElementById(`port_svcset_${index}`)?.value || '') : '',
            src_existing: srcMode === 'existing' ? (document.getElementById(`src_existing_${index}`)?.value || '') : '',
            dst_existing: dstMode === 'existing' ? (document.getElementById(`dst_existing_${index}`)?.value || '') : '',
            port_existing: portMode === 'existing' ? (document.getElementById(`port_existing_${index}`)?.value || '') : ''
        });
    });

    // 构建地址条目
    const srcEntries = parseIpInput(document.getElementById('src_ip').value);
    const dstEntries = parseIpInput(document.getElementById('dst_ip').value);
    const ports = parsePortInput(document.getElementById('port').value);

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                src_entries: srcEntries,
                dst_entries: dstEntries,
                ports: ports,
                protocol: analysisData.protocol,
                rule_name: document.getElementById('description').value,
                devices_config: devicesConfig
            })
        });

        const data = await response.json();

        if (data.success) {
            displayConfigResults(data.results);
            showStep(4);
        } else {
            alert('生成失败：' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('请求失败，请检查网络连接');
    }
}

// 解析 IP 输入
function parseIpInput(input) {
    const lines = input.split(/[,\n]/).map(s => s.trim()).filter(s => s);
    return lines.map(line => {
        if (line.includes('/')) {
            const [ip, mask] = line.split('/');
            return { ip: ip.trim(), mask: mask.trim() };
        }
        return { ip: line, mask: '32' };
    });
}

// 解析端口输入
function parsePortInput(input) {
    if (!input) return [];
    return input.split(',').map(s => s.trim()).filter(s => s);
}

// 显示配置结果
function displayConfigResults(results) {
    let html = '';
    results.forEach(result => {
        html += `
            <div class="config-result">
                <h4 style="color: #38ef7d; margin-bottom: 15px;">📋 ${result.device_name} (${result.vendor || '未知'})</h4>
                <pre>${result.config}</pre>
            </div>
        `;
    });
    document.getElementById('config_results').innerHTML = html;
}
