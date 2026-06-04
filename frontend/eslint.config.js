import pluginVue from 'eslint-plugin-vue'
import vuePrettier from '@vue/eslint-config-prettier'

export default [
  ...pluginVue.configs['flat/recommended'],
  vuePrettier,
  {
    rules: {
      'no-console': 'warn',
      'vue/multi-word-component-names': 'off',
    },
  },
]
