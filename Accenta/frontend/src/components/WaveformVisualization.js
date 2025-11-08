import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

const WaveformVisualization = ({ audioBlob, phrase, onRetry, onNext, attempts }) => {
  const svgRef = useRef(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [problemAreas, setProblemAreas] = useState([]);

  useEffect(() => {
    if (audioBlob) {
      const url = URL.createObjectURL(audioBlob);
      setAudioUrl(url);
      
      // Analyze audio and create waveform
      analyzeAudio(audioBlob);
      
      return () => URL.revokeObjectURL(url);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [audioBlob]);

  const analyzeAudio = async (blob) => {
    try {
      const arrayBuffer = await blob.arrayBuffer();
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
      
      // Extract waveform data
      const channelData = audioBuffer.getChannelData(0);
      const samples = 200; // Number of points to display
      const blockSize = Math.floor(channelData.length / samples);
      const waveform = [];
      
      for (let i = 0; i < samples; i++) {
        const start = i * blockSize;
        const end = start + blockSize;
        let sum = 0;
        for (let j = start; j < end; j++) {
          sum += Math.abs(channelData[j]);
        }
        waveform.push(sum / blockSize);
      }
      
      // Draw waveform
      drawWaveform(waveform);
      
      // Simulate problem areas (in production, this would come from backend analysis)
      const mockProblemAreas = [
        { start: 0.2, end: 0.3, issue: 'Vowel length too short', tip: 'Extend the vowel sound' },
        { start: 0.6, end: 0.7, issue: 'Consonant clarity', tip: 'Focus on tongue placement' },
      ];
      setProblemAreas(mockProblemAreas);
    } catch (error) {
      console.error('Error analyzing audio:', error);
    }
  };

  const drawWaveform = (waveform) => {
    if (!svgRef.current) return;
    
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();
    
    const width = svgRef.current.clientWidth || 800;
    const height = 200;
    const padding = 20;
    
    svg.attr('width', width).attr('height', height);
    
    const xScale = d3.scaleLinear()
      .domain([0, waveform.length - 1])
      .range([padding, width - padding]);
    
    const yScale = d3.scaleLinear()
      .domain([0, d3.max(waveform)])
      .range([height - padding, padding]);
    
    // Draw waveform
    const line = d3.line()
      .x((d, i) => xScale(i))
      .y((d) => yScale(d))
      .curve(d3.curveMonotoneX);
    
    svg.append('path')
      .datum(waveform)
      .attr('fill', 'none')
      .attr('stroke', '#6366f1')
      .attr('stroke-width', 2)
      .attr('d', line);
    
    // Highlight problem areas
    problemAreas.forEach((area) => {
      const startX = xScale(area.start * waveform.length);
      const endX = xScale(area.end * waveform.length);
      
      svg.append('rect')
        .attr('x', startX)
        .attr('y', padding)
        .attr('width', endX - startX)
        .attr('height', height - 2 * padding)
        .attr('fill', 'red')
        .attr('opacity', 0.2)
        .attr('class', 'problem-area')
        .on('mouseenter', function() {
          d3.select(this).attr('opacity', 0.4);
        })
        .on('mouseleave', function() {
          d3.select(this).attr('opacity', 0.2);
        });
    });
  };

  return (
    <div className="mt-8">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Recording</h3>
      
      {/* Waveform */}
      <div className="bg-gray-50 rounded-lg p-4 mb-4">
        <svg ref={svgRef} className="w-full" style={{ height: '200px' }} />
      </div>

      {/* Problem Areas Info */}
      {problemAreas.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Areas to Improve:</h4>
          <div className="space-y-2">
            {problemAreas.map((area, index) => (
              <div key={index} className="bg-red-50 border border-red-200 rounded p-3">
                <p className="text-sm font-medium text-red-800">{area.issue}</p>
                <p className="text-xs text-red-600 mt-1">💡 Tip: {area.tip}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Audio Playback */}
      {audioUrl && (
        <div className="mb-4">
          <audio controls src={audioUrl} className="w-full" />
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-4">
        {attempts < 3 ? (
          <button
            onClick={onRetry}
            className="flex-1 bg-yellow-500 text-white rounded-lg py-3 font-semibold hover:bg-yellow-600"
          >
            Try Again ({3 - attempts} attempts left)
          </button>
        ) : (
          <div className="flex-1 bg-gray-100 rounded-lg py-3 text-center text-gray-600">
            Maximum attempts reached
          </div>
        )}
        <button
          onClick={onNext}
          className="flex-1 bg-accenta-primary text-white rounded-lg py-3 font-semibold hover:bg-accenta-secondary"
        >
          Next Phrase
        </button>
      </div>
    </div>
  );
};

export default WaveformVisualization;

