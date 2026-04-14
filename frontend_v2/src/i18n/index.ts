import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import zhCommon from './locales/zh/common.json';
import zhHome from './locales/zh/home.json';
import zhDataset from './locales/zh/dataset.json';
import zhAnnotation from './locales/zh/annotation.json';
import zhTask from './locales/zh/task.json';
import zhDeploy from './locales/zh/deploy.json';
import zhAugment from './locales/zh/augment.json';
import zhTool from './locales/zh/tool.json';
import zhSettings from './locales/zh/settings.json';
import zhExample from './locales/zh/example.json';

import enCommon from './locales/en/common.json';
import enHome from './locales/en/home.json';
import enDataset from './locales/en/dataset.json';
import enAnnotation from './locales/en/annotation.json';
import enTask from './locales/en/task.json';
import enDeploy from './locales/en/deploy.json';
import enAugment from './locales/en/augment.json';
import enTool from './locales/en/tool.json';
import enSettings from './locales/en/settings.json';
import enExample from './locales/en/example.json';

const savedLang = localStorage.getItem('automl-lang') || 'zh';

i18n.use(initReactI18next).init({
    resources: {
        zh: {
            common: zhCommon,
            home: zhHome,
            dataset: zhDataset,
            annotation: zhAnnotation,
            task: zhTask,
            deploy: zhDeploy,
            augment: zhAugment,
            tool: zhTool,
            settings: zhSettings,
            example: zhExample,
        },
        en: {
            common: enCommon,
            home: enHome,
            dataset: enDataset,
            annotation: enAnnotation,
            task: enTask,
            deploy: enDeploy,
            augment: enAugment,
            tool: enTool,
            settings: enSettings,
            example: enExample,
        },
    },
    lng: savedLang,
    fallbackLng: 'zh',
    defaultNS: 'common',
    interpolation: {
        escapeValue: false,
    },
});

export default i18n;
