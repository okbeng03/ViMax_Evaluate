/**
 * Image preview component
 */

import { useState } from 'react';
import { Card, Image, Spin, message } from 'antd';

interface ImagePreviewProps {
  src?: string;
  alt?: string;
  height?: number | string;
}

export default function ImagePreview({
  src,
  alt = '预览图片',
  height = 300,
}: ImagePreviewProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  if (!src) {
    return (
      <Card style={{ height }}>
        <div
          style={{
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#999',
          }}
        >
          暂无图片
        </div>
      </Card>
    );
  }

  const handleError = () => {
    setError(true);
    setLoading(false);
    message.error('图片加载失败');
  };

  const handleLoad = () => {
    setLoading(false);
    setError(false);
  };

  return (
    <Card style={{ overflow: 'hidden' }}>
      <div style={{ position: 'relative', minHeight: height as number }}>
        {loading && (
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: '#f5f5f5',
            }}
          >
            <Spin />
          </div>
        )}
        <Image
          src={src}
          alt={alt}
          style={{ width: '100%', display: error ? 'none' : 'block' }}
          onError={handleError}
          onLoad={handleLoad}
          preview={{
            mask: <div>点击查看大图</div>,
          }}
        />
        {error && (
          <div
            style={{
              height: height as number,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: '#f5f5f5',
              color: '#999',
            }}
          >
            图片加载失败
          </div>
        )}
      </div>
    </Card>
  );
}
