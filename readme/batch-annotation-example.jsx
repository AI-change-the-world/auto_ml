import React from 'react';
import {
    Breadcrumb, Button, Card, Tag, Progress, Steps, Table, Input, Divider
} from 'antd';
import {
    ArrowLeftOutlined, SyncOutlined, CloseOutlined,
    PlayCircleFilled, CheckCircleFilled, CloseCircleFilled,
    ClockCircleOutlined, SearchOutlined, FilterOutlined
} from '@ant-design/icons';

const BatchAnnotation = () => {
    // 假数据：表格列表
    const dataSource = [
        { key: '1', name: 'image_001.jpg', status: 'success', time: '2.45s', error: '-', completedAt: '14:45:12' },
        { key: '2', name: 'image_002.jpg', status: 'success', time: '1.98s', error: '-', completedAt: '14:45:11' },
        { key: '3', name: 'image_003.jpg', status: 'error', time: '-', error: '模型推理异常', completedAt: '14:45:10' },
        { key: '4', name: 'image_004.jpg', status: 'success', time: '2.31s', error: '-', completedAt: '14:45:09' },
        { key: '5', name: 'image_005.jpg', status: 'pending', time: '-', error: '-', completedAt: '-' },
    ];

    // 表格列定义
    const columns = [
        { title: '文件名', dataIndex: 'name', key: 'name' },
        {
            title: '状态', dataIndex: 'status', key: 'status',
            render: (status) => {
                if (status === 'success') return <span className="text-green-500 flex items-center"><CheckCircleFilled className="mr-1" /> 成功</span>;
                if (status === 'error') return <span className="text-red-500 flex items-center"><CloseCircleFilled className="mr-1" /> 失败</span>;
                return <span className="text-gray-400 flex items-center"><ClockCircleOutlined className="mr-1" /> 待处理</span>;
            }
        },
        { title: '处理耗时', dataIndex: 'time', key: 'time' },
        { title: '错误信息', dataIndex: 'error', key: 'error' },
        { title: '完成时间', dataIndex: 'completedAt', key: 'completedAt' },
        {
            title: '', key: 'action',
            render: (_, record) => (
                <a className="text-blue-500 hover:text-blue-600">
                    {record.status === 'error' ? '查看详情' : (record.status === 'pending' ? '' : '查看结果')}
                </a>
            )
        },
    ];

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans">

            {/* 头部导航与操作区 */}
            <div className="flex justify-between items-start mb-6">
                <div>
                    <div className="flex items-center text-gray-500 mb-2">
                        <ArrowLeftOutlined className="mr-2 cursor-pointer hover:text-gray-800" />
                        <Breadcrumb separator="/">
                            <Breadcrumb.Item>批量标注</Breadcrumb.Item>
                            <Breadcrumb.Item>运行记录</Breadcrumb.Item>
                            <Breadcrumb.Item className="text-gray-800 font-medium">运行详情</Breadcrumb.Item>
                        </Breadcrumb>
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900 mb-1">运行详情</h1>
                    <p className="text-gray-500 text-sm">实时查看批量标注任务的执行进度、样本处理状态和运行日志</p>
                </div>
                <div className="flex space-x-3">
                    <Button icon={<SyncOutlined />}>刷新</Button>
                    <Button danger type="primary" icon={<CloseOutlined />}>取消任务</Button>
                </div>
            </div>

            {/* 顶部总览卡片 */}
            <Card className="mb-6 rounded-lg shadow-sm border-0">
                <div className="flex justify-between items-start">
                    <div className="flex items-start w-2/3">
                        {/* 图标 */}
                        <div className="w-16 h-16 bg-blue-100 text-blue-500 rounded-xl flex items-center justify-center mr-4 text-3xl shrink-0">
                            <PlayCircleFilled />
                        </div>

                        <div className="w-full">
                            {/* 标题与状态 */}
                            <div className="flex items-center mb-4">
                                <h2 className="text-xl font-bold mr-4">批量标注任务 #1024</h2>
                                <Tag color="blue" className="rounded-full px-3 text-blue-500 bg-blue-50 border-blue-200">
                                    <SyncOutlined spin className="mr-1" /> 执行中
                                </Tag>
                                <span className="text-gray-400 text-sm ml-2">已运行 00:12:45</span>
                            </div>

                            {/* 任务详情信息流 */}
                            <div className="grid grid-cols-6 gap-y-4 gap-x-2 text-sm">
                                <div>
                                    <div className="text-gray-500 mb-1">创建时间</div>
                                    <div className="text-gray-800">2025-07-28 14:30:22</div>
                                </div>
                                <div>
                                    <div className="text-gray-500 mb-1">开始时间</div>
                                    <div className="text-gray-800">2025-07-28 14:30:25</div>
                                </div>
                                <div>
                                    <div className="text-gray-500 mb-1">创建人</div>
                                    <div className="text-gray-800">张三</div>
                                </div>
                                <div>
                                    <div className="text-gray-500 mb-1">数据集</div>
                                    <a className="text-blue-500 hover:underline">工地安全隐患数据集</a>
                                </div>
                                <div>
                                    <div className="text-gray-500 mb-1">AI 流程</div>
                                    <div className="text-gray-800">安全帽检测流水线 v2</div>
                                </div>
                                <div>
                                    <div className="text-gray-500 mb-1">描述</div>
                                    <div className="text-gray-800">-</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <Divider className="my-5" />

                {/* 总体进度区 */}
                <div className="flex justify-between items-end">
                    <div className="w-1/2">
                        <div className="flex justify-between text-sm mb-1">
                            <span className="font-medium">总体进度</span>
                            <span className="text-blue-500 font-medium">66.7%</span>
                        </div>
                        <Progress percent={66.7} showInfo={false} strokeColor="#3b82f6" trailColor="#f1f5f9" className="m-0" />
                        <div className="text-gray-400 text-xs mt-1">已处理 1,670 / 2,500</div>
                    </div>

                    <div className="flex space-x-12">
                        <div className="text-center">
                            <div className="text-gray-500 text-sm mb-1">总样本数</div>
                            <div className="text-2xl font-bold text-gray-800">2,500</div>
                        </div>
                        <div className="text-center">
                            <div className="text-gray-500 text-sm mb-1">已完成</div>
                            <div className="text-2xl font-bold text-green-500">1,670</div>
                        </div>
                        <div className="text-center">
                            <div className="text-gray-500 text-sm mb-1">失败</div>
                            <div className="text-2xl font-bold text-red-500">25</div>
                        </div>
                        <div className="text-center">
                            <div className="text-gray-500 text-sm mb-1">待处理</div>
                            <div className="text-2xl font-bold text-gray-800">805</div>
                        </div>
                    </div>
                </div>
            </Card>

            <div className="flex flex-col lg:flex-row gap-6">
                {/* 左侧栏 */}
                <div className="w-full lg:w-1/3 flex flex-col gap-6">

                    {/* 运行状态卡片 */}
                    <Card title={<span className="font-bold text-base">运行状态</span>} bordered={false} className="rounded-lg shadow-sm">
                        <Steps
                            direction="vertical"
                            current={3}
                            size="small"
                            items={[
                                { title: <div className="flex justify-between w-full"><span className="text-gray-800">任务开始执行</span><span className="text-gray-400 font-normal">14:30:25</span></div>, description: '批量标注任务已开始' },
                                { title: <div className="flex justify-between w-full"><span className="text-gray-800">数据加载完成</span><span className="text-gray-400 font-normal">14:30:28</span></div>, description: '成功加载 2,500 个样本' },
                                { title: <div className="flex justify-between w-full"><span className="text-gray-800">模型推理中</span><span className="text-gray-400 font-normal">14:30:30</span></div>, description: '正在对样本进行推理' },
                                { title: <div className="flex justify-between w-full"><span className="text-blue-500 font-medium">样本处理中</span><span className="text-gray-400 font-normal">14:43:10</span></div>, description: '已处理 1,670 / 2,500' },
                                { title: <div className="flex justify-between w-full"><span className="text-gray-400">等待中</span><span className="text-gray-400 font-normal">-</span></div>, description: '还有 805 个样本待处理' },
                            ]}
                        />
                        <Button block className="mt-4 text-blue-500 border-gray-200">查看全部日志</Button>
                    </Card>

                    {/* 任务信息卡片 */}
                    <Card title={<span className="font-bold text-base">任务信息</span>} bordered={false} className="rounded-lg shadow-sm">
                        <div className="space-y-4 text-sm">
                            <div className="flex justify-between"><span className="text-gray-500">运行 ID</span><span className="text-gray-800">1024</span></div>
                            <Divider className="my-0 border-gray-100" />
                            <div className="flex justify-between items-center"><span className="text-gray-500">状态</span><Tag color="blue" className="m-0 rounded border-0 bg-blue-50 text-blue-500">执行中</Tag></div>
                            <Divider className="my-0 border-gray-100" />
                            <div className="flex justify-between items-center"><span className="text-gray-500">优先级</span><Tag className="m-0 bg-gray-100 border-0 text-gray-600">中</Tag></div>
                            <Divider className="my-0 border-gray-100" />
                            <div className="flex justify-between"><span className="text-gray-500">并发数</span><span className="text-gray-800">4</span></div>
                            <Divider className="my-0 border-gray-100" />
                            <div className="flex justify-between"><span className="text-gray-500">重试次数</span><span className="text-gray-800">2</span></div>
                            <Divider className="my-0 border-gray-100" />
                            <div className="flex justify-between"><span className="text-gray-500">备注</span><span className="text-gray-800">-</span></div>
                        </div>
                    </Card>
                </div>

                {/* 右侧栏 */}
                <div className="w-full lg:w-2/3 flex flex-col gap-6">

                    {/* 样本处理结果卡片 */}
                    <Card title={<span className="font-bold text-base">样本处理结果</span>} bordered={false} className="rounded-lg shadow-sm">
                        <div className="flex items-center justify-between">

                            {/* 饼图与图例模拟区 */}
                            <div className="flex items-center w-1/2 px-4">
                                {/* 简易纯CSS圆环图占位 */}
                                <div className="relative w-36 h-36 rounded-full border-[12px] border-green-400 mr-8 flex items-center justify-center" style={{ borderRightColor: '#F1F5F9', borderBottomColor: '#F1F5F9', transform: 'rotate(-45deg)' }}>
                                    <div style={{ transform: 'rotate(45deg)' }} className="text-center">
                                        <div className="text-2xl font-bold text-gray-800">2,500</div>
                                        <div className="text-xs text-gray-500">总样本数</div>
                                    </div>
                                </div>

                                {/* 图例 */}
                                <div className="space-y-3 flex-1 text-sm">
                                    <div className="flex justify-between items-center">
                                        <div><span className="inline-block w-2 h-2 rounded-full bg-green-500 mr-2"></span>成功</div>
                                        <div className="text-gray-600">1,670 (66.7%)</div>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <div><span className="inline-block w-2 h-2 rounded-full bg-red-500 mr-2"></span>失败</div>
                                        <div className="text-gray-600">25 (1.0%)</div>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <div><span className="inline-block w-2 h-2 rounded-full bg-gray-300 mr-2"></span>待处理</div>
                                        <div className="text-gray-600">805 (32.3%)</div>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <div><span className="inline-block w-2 h-2 rounded-full bg-yellow-500 mr-2"></span>已跳过</div>
                                        <div className="text-gray-600">0 (0.0%)</div>
                                    </div>
                                </div>
                            </div>

                            {/* 拆线图模拟区 */}
                            <div className="w-1/2 px-4 border-l border-gray-100 relative h-40">
                                <div className="flex justify-between items-center mb-2 text-sm">
                                    <span className="text-gray-600">处理速度 (样本/分钟)</span>
                                    <span className="text-gray-400 text-xs text-right">当前速度<br /><span className="text-blue-500 font-bold text-sm">98 样本/分钟</span></span>
                                </div>
                                {/* 占位折线图 */}
                                <div className="w-full h-24 bg-gradient-to-t from-blue-50 to-transparent relative border-b border-gray-200 flex items-end">
                                    {/* SVG 模拟折线 */}
                                    <svg viewBox="0 0 100 40" className="w-full h-full preserve-3d" preserveAspectRatio="none">
                                        <path d="M0,20 Q10,25 20,20 T40,10 T60,20 T80,10 T100,15" fill="none" stroke="#3b82f6" strokeWidth="1.5" />
                                        <circle cx="100" cy="15" r="1.5" fill="#3b82f6" />
                                    </svg>
                                    {/* Y轴标签 */}
                                    <div className="absolute left-0 bottom-0 text-[10px] text-gray-400 flex flex-col justify-between h-full py-1">
                                        <span>120</span><span>90</span><span>60</span><span>30</span><span>0</span>
                                    </div>
                                </div>
                                {/* X轴标签 */}
                                <div className="flex justify-between text-[10px] text-gray-400 mt-1 pl-6">
                                    <span>14:30</span><span>14:35</span><span>14:40</span><span>14:45</span>
                                </div>
                            </div>

                        </div>
                    </Card>

                    {/* 样本处理列表卡片 */}
                    <Card title={<span className="font-bold text-base">样本处理列表</span>} bordered={false} className="rounded-lg shadow-sm flex-1">

                        {/* 过滤器 & 搜索 */}
                        <div className="flex justify-between items-center mb-4">
                            <div className="flex space-x-6 text-sm">
                                <div className="text-blue-500 border-b-2 border-blue-500 pb-2 font-medium cursor-pointer">全部 <span className="text-blue-400">2,500</span></div>
                                <div className="text-gray-600 cursor-pointer pb-2 hover:text-gray-800">成功 <span className="text-green-500 bg-green-50 px-1 rounded">1,670</span></div>
                                <div className="text-gray-600 cursor-pointer pb-2 hover:text-gray-800">失败 <span className="text-red-500 bg-red-50 px-1 rounded">25</span></div>
                                <div className="text-gray-600 cursor-pointer pb-2 hover:text-gray-800">待处理 <span className="text-gray-500 bg-gray-100 px-1 rounded">805</span></div>
                                <div className="text-gray-600 cursor-pointer pb-2 hover:text-gray-800">已跳过 <span className="text-yellow-600 bg-yellow-50 px-1 rounded">0</span></div>
                            </div>
                            <div className="flex space-x-2">
                                <Input placeholder="搜索文件名" prefix={<SearchOutlined className="text-gray-400" />} className="w-48" />
                                <Button icon={<FilterOutlined />} />
                            </div>
                        </div>

                        {/* 表格 */}
                        <Table
                            dataSource={dataSource}
                            columns={columns}
                            pagination={false}
                            size="middle"
                            className="mb-4"
                        />

                        {/* 自定义分页组件 (底部) */}
                        <div className="flex justify-between items-center text-sm text-gray-500 mt-4">
                            <div>
                                共 2,500 条 <span className="mx-2 px-2 py-1 border rounded bg-white cursor-pointer">50 条/页 ▾</span>
                            </div>
                            <div className="flex items-center space-x-1">
                                <Button size="small" type="text" disabled> {'<'} </Button>
                                <Button size="small" type="primary" className="bg-blue-50 text-blue-500 border-blue-200">1</Button>
                                <Button size="small" type="text">2</Button>
                                <Button size="small" type="text">3</Button>
                                <Button size="small" type="text">4</Button>
                                <Button size="small" type="text">5</Button>
                                <span className="px-1">...</span>
                                <Button size="small" type="text">50</Button>
                                <Button size="small" type="text"> {'>'} </Button>
                                <span className="ml-2">前往</span>
                                <Input size="small" className="w-10 text-center mx-1" defaultValue="1" />
                                <span>页</span>
                            </div>
                        </div>

                    </Card>
                </div>
            </div>
        </div>
    );
};

export default BatchAnnotation;
