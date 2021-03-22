import { nodeResolve } from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import { babel } from '@rollup/plugin-babel';

export default {
  input: 'src/index.js',
  output: {
    dir: 'output',
    format: 'iife'
  },
  plugins: [
    nodeResolve(),
    // commonjs()
  ]
};
