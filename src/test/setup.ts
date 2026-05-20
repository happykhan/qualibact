import '@testing-library/jest-dom';

// mock next/image to render simple img tags in tests
import React from 'react';
import type { FC, ImgHTMLAttributes } from 'react';
const NextImage: FC<ImgHTMLAttributes<HTMLImageElement>> = (props) => {
  // eslint-disable-next-line jsx-a11y/alt-text
  return React.createElement('img', props as any);
};

Object.defineProperty(global, 'Image', {
  value: class MockImage {
    constructor() {
      // no-op
    }
    set src(_v: string) {}
  }
});

vi.mock('next/image', () => ({
  default: (props: any) => {
    return React.createElement('img', props as any);
  }
}));
