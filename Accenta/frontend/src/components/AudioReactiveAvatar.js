import React, { useEffect, useRef, useState } from 'react';

const AudioReactiveAvatar = ({ audioBlob, isSpeaking, onAnimationComplete }) => {
  const canvasRef = useRef(null);
  const animationFrameRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const dataArrayRef = useRef(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [winkProgress, setWinkProgress] = useState(0); // 0 = open, 1 = fully closed
  const hasWinkedRef = useRef(false);
  const idleAnimationRef = useRef(null);
  const winkProgressRef = useRef(0); // Ref to track latest winkProgress for animation loop

  // Draw function - defined before use
  const draw = (ctx, width, height, level, dataArray = null, winkProgress = 0) => {
    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    const centerX = width / 2;
    const centerY = height / 2;
    const baseRadius = 80;
    const maxRadius = baseRadius + (level * 120); // React to audio

    // Create gradient
    const gradient = ctx.createRadialGradient(centerX, centerY, baseRadius, centerX, centerY, maxRadius);
    gradient.addColorStop(0, `rgba(99, 102, 241, ${0.8 + level * 0.2})`); // Indigo
    gradient.addColorStop(0.5, `rgba(139, 92, 246, ${0.6 + level * 0.3})`); // Purple
    gradient.addColorStop(1, `rgba(236, 72, 153, ${0.3 + level * 0.2})`); // Pink

    // Main pulsing circle (avatar representation)
    ctx.beginPath();
    ctx.arc(centerX, centerY, maxRadius, 0, Math.PI * 2);
    ctx.fillStyle = gradient;
    ctx.fill();

    // Add ripple effects based on audio
    const rippleCount = Math.floor(level * 5) + 1;
    for (let i = 0; i < rippleCount; i++) {
      const rippleRadius = maxRadius + (i * 20);
      const opacity = (1 - (i / rippleCount)) * (0.3 + level * 0.2);
      
      ctx.beginPath();
      ctx.arc(centerX, centerY, rippleRadius, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(99, 102, 241, ${opacity})`;
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // Add frequency bars around the circle
    if (dataArray) {
      const barCount = 32;
      
      for (let i = 0; i < barCount; i++) {
        const angle = (i / barCount) * Math.PI * 2;
        const dataIndex = Math.floor((i / barCount) * dataArray.length);
        const barHeight = (dataArray[dataIndex] / 255) * 60;
        
        const x1 = centerX + Math.cos(angle) * maxRadius;
        const y1 = centerY + Math.sin(angle) * maxRadius;
        const x2 = centerX + Math.cos(angle) * (maxRadius + barHeight);
        const y2 = centerY + Math.sin(angle) * (maxRadius + barHeight);
        
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.strokeStyle = `rgba(255, 255, 255, ${0.6 + level * 0.4})`;
        ctx.lineWidth = 3;
        ctx.stroke();
      }
    }

    // Face/expression (simple representation)
    const eyeSize = 8 + level * 4;
    const eyeOffsetX = 25;
    const eyeOffsetY = -15;
    
    // Left eye (normal)
    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.beginPath();
    ctx.arc(centerX - eyeOffsetX, centerY + eyeOffsetY, eyeSize, 0, Math.PI * 2);
    ctx.fill();
    
    // Right eye (winking - draw as a line when winking)
    if (winkProgress > 0) {
      // Draw winking eye as a curved line
      const winkHeight = eyeSize * winkProgress;
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(centerX + eyeOffsetX, centerY + eyeOffsetY, eyeSize / 2, 0, Math.PI);
      ctx.stroke();
    } else {
      // Normal open eye
      ctx.beginPath();
      ctx.arc(centerX + eyeOffsetX, centerY + eyeOffsetY, eyeSize, 0, Math.PI * 2);
      ctx.fill();
    }

    // Mouth (smile that reacts to audio)
    const mouthWidth = 30 + level * 20;
    ctx.beginPath();
    ctx.arc(centerX, centerY + 20, mouthWidth / 2, 0, Math.PI);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.lineWidth = 3;
    ctx.stroke();
  };

  // Wink animation on mount
  useEffect(() => {
    if (hasWinkedRef.current) return;
    
    const winkDuration = 300; // 300ms for wink
    const startTime = Date.now();
    
    const animateWink = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(1, elapsed / winkDuration);
      
      // Easing function for smooth wink (ease in-out)
      const easedProgress = progress < 0.5
        ? 2 * progress * progress
        : 1 - Math.pow(-2 * progress + 2, 2) / 2;
      
      setWinkProgress(easedProgress);
      winkProgressRef.current = easedProgress; // Update ref for animation loop
      
      if (progress < 1) {
        requestAnimationFrame(animateWink);
      } else {
        // Wink complete
        setWinkProgress(0);
        winkProgressRef.current = 0;
        hasWinkedRef.current = true;
      }
    };
    
    // Start wink animation after a short delay
    const timeout = setTimeout(() => {
      animateWink();
    }, 500); // Wait 500ms after mount
    
    return () => clearTimeout(timeout);
  }, []);

  useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    canvas.width = 400;
    canvas.height = 400;

    // Draw idle state if no audio (include wink progress)
    if (!audioBlob) {
      draw(ctx, canvas.width, canvas.height, 0.2, null, winkProgress);
      
      // Keep animating the idle state (for wink animation)
      // Use ref to read latest winkProgress value in animation loop
      const idleAnimation = () => {
        if (!audioBlob && canvasRef.current) {
          // Read latest winkProgress from ref (updated by wink animation)
          draw(ctx, canvas.width, canvas.height, 0.2, null, winkProgressRef.current);
          idleAnimationRef.current = requestAnimationFrame(idleAnimation);
        }
      };
      idleAnimationRef.current = requestAnimationFrame(idleAnimation);
      return;
    }

    // Initialize audio context and analyser
    const initAudio = async () => {
      try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.8;
        
        // Decode audio blob to AudioBuffer
        const arrayBuffer = await audioBlob.arrayBuffer();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        
        // Create buffer source
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        
        // Connect to analyser and destination
        source.connect(analyser);
        analyser.connect(audioContext.destination);

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        audioContextRef.current = audioContext;
        analyserRef.current = analyser;
        dataArrayRef.current = dataArray;

        setIsPlaying(true);

        // Animation loop
        const animate = () => {
          if (!isPlaying) return;

          analyser.getByteFrequencyData(dataArray);
          
          // Calculate average audio level
          let sum = 0;
          for (let i = 0; i < bufferLength; i++) {
            sum += dataArray[i];
          }
          const average = sum / bufferLength;
          const normalizedLevel = Math.min(1, average / 255);
          
          setAudioLevel(normalizedLevel);

          // Draw animation with frequency data (include wink progress)
          draw(ctx, canvas.width, canvas.height, normalizedLevel, dataArray, winkProgress);

          animationFrameRef.current = requestAnimationFrame(animate);
        };

        animate();

        source.onended = () => {
          setIsPlaying(false);
          if (onAnimationComplete) {
            onAnimationComplete();
          }
          // Cleanup
          if (animationFrameRef.current) {
            cancelAnimationFrame(animationFrameRef.current);
          }
          // Draw final state (include wink progress)
          draw(ctx, canvas.width, canvas.height, 0, null, winkProgress);
        };

        source.start(0);

      } catch (error) {
        console.error('Error initializing audio:', error);
        setIsPlaying(false);
        // Fallback: draw static avatar (include wink progress)
        draw(ctx, canvas.width, canvas.height, 0.3, null, winkProgress);
      }
    };

    initAudio();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (idleAnimationRef.current) {
        cancelAnimationFrame(idleAnimationRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, [audioBlob, onAnimationComplete, winkProgress]);

  return (
    <div className="flex flex-col items-center justify-center">
      <canvas
        ref={canvasRef}
        className="rounded-full shadow-2xl"
        style={{
          background: 'radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
        }}
      />
      {isSpeaking && (
        <div className="mt-4 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-500/20 rounded-full">
            <div className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-indigo-700 font-medium">Wally is speaking...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default AudioReactiveAvatar;

