<template>
  <div class="project-create">
    <!-- 页面头部 -->
    <div class="header">
      <el-button type="text" @click="$router.back()" class="back-btn">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h1>创建项目</h1>
    </div>

    <!-- 创建表单 -->
    <div class="form-container">
      <el-card class="form-card">
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-width="100px"
          label-position="top"
          @submit.prevent="handleSubmit"
        >
          <!-- 项目名称 -->
          <el-form-item label="项目名称" prop="project_name">
            <el-input
              v-model="form.project_name"
              placeholder="请输入项目名称"
              maxlength="100"
              show-word-limit
              clearable
            />
            <div class="form-tip">
              项目名称将作为最终导出文档的标题
            </div>
          </el-form-item>

          <!-- 项目类型 -->
          <el-form-item label="项目类型" prop="project_type">
            <el-radio-group v-model="form.project_type" class="project-type-group">
              <el-card
                class="type-card"
                :class="{ active: form.project_type === 'code' }"
                @click="form.project_type = 'code'"
              >
                <el-radio value="code" class="type-radio">
                  <div class="type-content">
                    <div class="type-icon">
                      <el-icon size="32"><Document /></el-icon>
                    </div>
                    <div class="type-info">
                      <h3>代码文件构建</h3>
                      <p>上传源代码文件，自动生成带语法高亮的代码文档</p>
                      <ul class="type-features">
                        <li>支持多种编程语言</li>
                        <li>自动语法高亮</li>
                        <li>连续行号编排</li>
                        <li>文件顺序调整</li>
                      </ul>
                    </div>
                  </div>
                </el-radio>
              </el-card>

              <el-card
                class="type-card"
                :class="{ active: form.project_type === 'manual' }"
                @click="form.project_type = 'manual'"
              >
                <el-radio value="manual" class="type-radio">
                  <div class="type-content">
                    <div class="type-icon">
                      <el-icon size="32"><Notebook /></el-icon>
                    </div>
                    <div class="type-info">
                      <h3>操作文档构建</h3>
                      <p>创建图文并茂的软件操作说明文档</p>
                      <ul class="type-features">
                        <li>模板化文档结构</li>
                        <li>图文章节编辑</li>
                        <li>Markdown 支持</li>
                        <li>全局变量替换</li>
                      </ul>
                    </div>
                  </div>
                </el-radio>
              </el-card>
            </el-radio-group>
          </el-form-item>

          <!-- 代码项目配置选项 -->
          <div v-if="form.project_type === 'code'" class="code-project-config">
            <el-divider content-position="left">代码项目配置</el-divider>

            <!-- 代码格式化选项 -->
            <el-form-item label="代码格式化">
              <el-checkbox-group v-model="form.code_options.formatting">
                <el-checkbox value="line_numbers">显示行号</el-checkbox>
                <el-checkbox value="highlight_syntax">语法高亮</el-checkbox>
                <el-checkbox value="wrap_lines">自动换行</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <!-- 页面布局选项 -->
            <el-form-item label="页面布局">
              <el-radio-group v-model="form.code_options.layout">
                <el-radio value="single_column">单列布局</el-radio>
                <el-radio value="double_column">双列布局</el-radio>
              </el-radio-group>
              <div class="form-tip">
                双列布局适合代码量较大的项目，可以更好地利用页面空间
              </div>
            </el-form-item>

            <!-- 字体设置 -->
            <el-form-item label="字体大小">
              <el-select v-model="form.code_options.font_size" placeholder="选择字体大小">
                <el-option label="小号 (12px)" value="12px" />
                <el-option label="中号 (14px)" value="14px" />
                <el-option label="大号 (16px)" value="16px" />
              </el-select>
            </el-form-item>

            <!-- 导出选项 -->
            <el-form-item label="导出选项">
              <el-checkbox-group v-model="form.code_options.export_options">
                <el-checkbox value="include_toc">包含目录</el-checkbox>
                <el-checkbox value="include_summary">包含统计信息</el-checkbox>
                <el-checkbox value="watermark">添加水印</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </div>

          <!-- 操作文档项目配置选项 -->
          <div v-if="form.project_type === 'manual'" class="manual-project-config">
            <el-divider content-position="left">操作文档配置</el-divider>

            <!-- 文档模板 -->
            <el-form-item label="文档模板">
              <el-select v-model="form.manual_options.template" placeholder="选择文档模板">
                <el-option label="标准模板" value="standard" />
                <el-option label="详细模板" value="detailed" />
                <el-option label="简洁模板" value="simple" />
              </el-select>
              <div class="form-tip">
                不同模板包含不同的预设章节结构
              </div>
            </el-form-item>

            <!-- 章节配置 -->
            <el-form-item label="默认章节">
              <el-checkbox-group v-model="form.manual_options.default_sections">
                <el-checkbox value="overview">软件概述</el-checkbox>
                <el-checkbox value="installation">安装说明</el-checkbox>
                <el-checkbox value="usage">使用说明</el-checkbox>
                <el-checkbox value="features">功能介绍</el-checkbox>
                <el-checkbox value="troubleshooting">常见问题</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </div>

          <!-- 操作按钮 -->
          <el-form-item>
            <div class="form-actions">
              <el-button @click="$router.back()">取消</el-button>
              <el-button
                type="primary"
                @click="handleSubmit"
                :loading="loading"
                :disabled="!form.project_name || !form.project_type"
              >
                创建项目
              </el-button>
            </div>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { ArrowLeft, Document, Notebook } from '@element-plus/icons-vue'
import type { ProjectCreateRequest } from '@/types'
import { projectApi } from '@/utils/api'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)

// 表单数据
const form = reactive({
  project_name: '',
  project_type: 'code',
  code_options: {
    formatting: ['line_numbers', 'highlight_syntax'],
    layout: 'single_column',
    font_size: '14px',
    export_options: ['include_toc']
  },
  manual_options: {
    template: 'standard',
    default_sections: ['overview', 'installation', 'usage']
  }
})

// 表单验证规则
const rules: FormRules = {
  project_name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 1, max: 100, message: '项目名称长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  project_type: [
    { required: true, message: '请选择项目类型', trigger: 'change' }
  ]
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    loading.value = true

    // 准备提交数据
    const submitData: any = {
      project_name: form.project_name,
      project_type: form.project_type
    }

    // 根据项目类型添加配置选项
    if (form.project_type === 'code') {
      submitData.code_options = form.code_options
    } else if (form.project_type === 'manual') {
      submitData.manual_options = form.manual_options
    }

    const response = await projectApi.createProject(submitData)

    if (response.code === 0) {
      ElMessage.success('项目创建成功')
      // 跳转到项目详情页
      const projectId = response.data.id
      router.push(`/projects/${projectId}`)
    } else {
      ElMessage.error(response.message || '创建项目失败')
    }
  } catch (error) {
    console.error('创建项目失败:', error)
    ElMessage.error('创建项目失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.project-create {
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
}

.header {
  display: flex;
  align-items: center;
  margin-bottom: 32px;
}

.back-btn {
  margin-right: 16px;
  padding: 8px;
}

.header h1 {
  margin: 0;
  color: #111;
  font-size: 28px;
  font-weight: 600;
}

.form-container {
  width: 100%;
}

.form-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.form-tip {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.project-type-group {
  width: 100%;
}

.project-type-group .el-radio {
  width: 100%;
  margin-right: 0;
  margin-bottom: 16px;
}

.project-type-group .el-radio:last-child {
  margin-bottom: 0;
}

.type-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid #e4e7ed;
  margin-bottom: 16px;
}

.type-card:hover {
  border-color: #5c7cfa;
  box-shadow: 0 4px 12px rgba(92, 124, 250, 0.15);
}

.type-card.active {
  border-color: #5c7cfa;
  background-color: #f8f9ff;
}

.type-radio {
  width: 100%;
}

.type-radio .el-radio__input {
  display: none;
}

.type-radio .el-radio__label {
  width: 100%;
  padding: 0;
}

.type-content {
  display: flex;
  align-items: flex-start;
  padding: 20px;
}

.type-icon {
  margin-right: 20px;
  color: #5c7cfa;
  flex-shrink: 0;
}

.type-info {
  flex: 1;
}

.type-info h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #111;
}

.type-info p {
  margin: 0 0 12px 0;
  color: #666;
  font-size: 14px;
  line-height: 1.5;
}

.type-features {
  margin: 0;
  padding: 0;
  list-style: none;
}

.type-features li {
  position: relative;
  padding-left: 16px;
  margin-bottom: 4px;
  font-size: 12px;
  color: #888;
}

.type-features li:before {
  content: '•';
  position: absolute;
  left: 0;
  color: #5c7cfa;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}
</style>
