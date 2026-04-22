/**
 * Advanced Features Module for FaceAttend AI
 * Additional utilities and enhancements
 */

// ──── EXPORT UTILITIES ───────────────────────────────────────────────

class ReportGenerator {
  static generateCSV(data, filename = 'report.csv') {
    let csv = 'Student ID,Name,Roll,Branch,Total Days,Present,Percentage\n';
    data.forEach(row => {
      csv += `${row.student_id},${row.name},${row.roll_number},"${row.branch}",${row.total_days},${row.present},${row.attendance_percentage}\n`;
    });
    this.download(csv, filename, 'text/csv');
  }

  static async generatePDF(data, filename = 'report.pdf') {
    // Requires jsPDF library: https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js
    const doc = new jsPDF();
    const pageHeight = doc.internal.pageSize.getHeight();
    const pageWidth = doc.internal.pageSize.getWidth();
    const margin = 10;
    let yPosition = margin;

    // Title
    doc.setFontSize(18);
    doc.text('Attendance Report', margin, yPosition);
    yPosition += 10;

    // Meta information
    doc.setFontSize(10);
    doc.text(`Generated: ${new Date().toLocaleString()}`, margin, yPosition);
    yPosition += 8;

    // Table
    doc.setFontSize(9);
    const headers = ['ID', 'Name', 'Branch', 'Days', 'Present', '%'];
    const headerX = [margin, margin + 20, margin + 50, margin + 80, margin + 100, margin + 125];
    const headerY = yPosition;

    headers.forEach((header, i) => {
      doc.text(header, headerX[i], headerY);
    });

    yPosition += 8;
    doc.setDrawColor(200);
    doc.line(margin, yPosition, pageWidth - margin, yPosition);
    yPosition += 2;

    // Data rows
    data.forEach(row => {
      if (yPosition > pageHeight - 20) {
        doc.addPage();
        yPosition = margin;
      }

      const values = [
        row.student_id,
        row.name.substring(0, 15),
        row.branch,
        row.total_days,
        row.present,
        row.attendance_percentage + '%'
      ];

      values.forEach((value, i) => {
        doc.text(String(value), headerX[i], yPosition);
      });

      yPosition += 7;
    });

    doc.save(filename);
  }

  static generateExcel(data, filename = 'report.xlsx') {
    // Requires SheetJS: https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.min.js
    const worksheet = XLSX.utils.json_to_sheet(data);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Attendance');
    XLSX.writeFile(workbook, filename);
  }

  static download(content, filename, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
}

// ──── ANALYTICS MODULE ──────────────────────────────────────────────

class AttendanceAnalytics {
  static calculateStatistics(records) {
    const stats = {
      totalRecords: records.length,
      uniqueStudents: new Set(records.map(r => r.student_id)).size,
      averageConfidence: 0,
      confidenceDistribution: {},
      attendanceByHour: {},
      peakHours: [],
      lowAttendanceStudents: []
    };

    if (records.length === 0) return stats;

    // Average confidence
    const confidenceSum = records.reduce((sum, r) => sum + (r.confidence || 0), 0);
    stats.averageConfidence = (confidenceSum / records.length * 100).toFixed(2);

    // Confidence distribution
    records.forEach(r => {
      const conf = Math.floor(r.confidence * 10) * 10;
      stats.confidenceDistribution[conf] = (stats.confidenceDistribution[conf] || 0) + 1;
    });

    // Attendance by hour
    records.forEach(r => {
      const hour = new Date(r.timestamp).getHours();
      stats.attendanceByHour[hour] = (stats.attendanceByHour[hour] || 0) + 1;
    });

    // Peak hours
    stats.peakHours = Object.entries(stats.attendanceByHour)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([hour, count]) => ({ hour: `${hour}:00`, count }));

    return stats;
  }

  static generateChartData(students) {
    return {
      labels: students.map(s => s.name.split(' ')[0]),
      datasets: [{
        label: 'Attendance %',
        data: students.map(s => {
          const records = s.attendance_records || [];
          return records.length > 0 ? (records.filter(r => r.status === 'present').length / records.length * 100) : 0;
        }),
        backgroundColor: 'rgba(0, 212, 170, 0.5)',
        borderColor: 'rgba(0, 212, 170, 1)',
        borderWidth: 1
      }]
    };
  }
}

// ──── FACE DETECTION ENHANCEMENT ────────────────────────────────────

class FaceDetectionEngine {
  static async loadModel() {
    // Load face detection model (TensorFlow.js or custom)
    // Requires: https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd
    console.log('Face detection model loaded');
  }

  static async detectFaces(imageData) {
    // Placeholder for advanced face detection
    return {
      faces: [],
      confidence: 0
    };
  }

  static validateFaceQuality(canvas) {
    const ctx = canvas.getContext('2d');
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;

    let brightness = 0;
    for (let i = 0; i < data.length; i += 4) {
      brightness += (data[i] + data[i + 1] + data[i + 2]) / 3;
    }
    brightness /= (data.length / 4);

    return {
      quality: brightness > 50 && brightness < 200 ? 'good' : 'poor',
      brightness: Math.round(brightness)
    };
  }
}

// ──── NOTIFICATION SYSTEM ──────────────────────────────────────────

class NotificationManager {
  static queue = [];

  static add(notification) {
    this.queue.push({
      ...notification,
      timestamp: new Date(),
      id: Math.random()
    });
  }

  static getRecent(count = 10) {
    return this.queue.slice(-count);
  }

  static clearOld(minutesOld = 60) {
    const cutoff = Date.now() - (minutesOld * 60 * 1000);
    this.queue = this.queue.filter(n => n.timestamp.getTime() > cutoff);
  }

  static exportLog() {
    const log = this.queue.map(n => 
      `[${n.timestamp.toISOString()}] ${n.type.toUpperCase()}: ${n.title} - ${n.body}`
    ).join('\n');
    
    const blob = new Blob([log], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `notifications-${Date.now()}.log`;
    a.click();
    URL.revokeObjectURL(url);
  }
}

// ──── PERFORMANCE MONITORING ────────────────────────────────────────

class PerformanceMonitor {
  static metrics = {
    apiCalls: [],
    cameraFrames: 0,
    faceDetections: 0,
    recognitionTime: []
  };

  static recordAPICall(endpoint, duration, success) {
    this.metrics.apiCalls.push({
      endpoint,
      duration,
      success,
      timestamp: new Date()
    });
  }

  static recordRecognitionTime(duration) {
    this.metrics.recognitionTime.push(duration);
  }

  static getPerformanceReport() {
    const apiStats = this.metrics.apiCalls;
    const avgAPITime = apiStats.length > 0 
      ? (apiStats.reduce((sum, c) => sum + c.duration, 0) / apiStats.length).toFixed(2)
      : 0;

    const recTimeStats = this.metrics.recognitionTime;
    const avgRecTime = recTimeStats.length > 0
      ? (recTimeStats.reduce((sum, t) => sum + t, 0) / recTimeStats.length).toFixed(2)
      : 0;

    return {
      totalAPIRequests: apiStats.length,
      averageAPITime: avgAPITime,
      successRate: apiStats.length > 0 
        ? (apiStats.filter(c => c.success).length / apiStats.length * 100).toFixed(1)
        : 0,
      totalFaceDetections: this.metrics.faceDetections,
      averageRecognitionTime: avgRecTime,
      cameraFramesProcessed: this.metrics.cameraFrames
    };
  }

  static exportMetrics() {
    const report = this.getPerformanceReport();
    console.table(report);
    return report;
  }
}

// ──── DATA BACKUP & RECOVERY ────────────────────────────────────────

class DataBackupManager {
  static backup() {
    const data = {
      students: localStorage.getItem('students'),
      settings: localStorage.getItem('settings'),
      timestamp: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `faceattend-backup-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);

    return data;
  }

  static restore(fileInput) {
    const file = fileInput.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result);
        if (data.students) localStorage.setItem('students', data.students);
        if (data.settings) localStorage.setItem('settings', data.settings);
        alert('✅ Backup restored successfully');
        location.reload();
      } catch (err) {
        alert('❌ Invalid backup file: ' + err.message);
      }
    };
    reader.readAsText(file);
  }

  static autoBackup(intervalMinutes = 60) {
    setInterval(() => {
      this.backup();
      console.log('🔄 Auto backup completed');
    }, intervalMinutes * 60 * 1000);
  }
}

// ──── ACCESSIBILITY FEATURES ────────────────────────────────────────

class A11yEnhancements {
  static enableScreenReaderMode() {
    const style = document.createElement('style');
    style.textContent = `
      .visually-hidden {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border-width: 0;
      }
    `;
    document.head.appendChild(style);
  }

  static announceToScreenReader(message) {
    const announcement = document.createElement('div');
    announcement.className = 'visually-hidden';
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.textContent = message;
    document.body.appendChild(announcement);
    setTimeout(() => announcement.remove(), 3000);
  }

  static enableKeyboardNavigation() {
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        // Close any open modals
        document.querySelectorAll('.modal.active').forEach(m => {
          m.classList.remove('active');
        });
      }
    });
  }
}

// ──── EXPORT MODULE FUNCTIONS ────────────────────────────────────────

// Usage examples:
// ReportGenerator.generateCSV(data, 'attendance.csv');
// ReportGenerator.generatePDF(data, 'attendance.pdf');
// ReportGenerator.generateExcel(data, 'attendance.xlsx');

// const stats = AttendanceAnalytics.calculateStatistics(records);
// const peakHours = stats.peakHours;

// PerformanceMonitor.recordAPICall('/api/students', 150, true);
// const report = PerformanceMonitor.getPerformanceReport();
// console.log(report);

// DataBackupManager.autoBackup(60);
// DataBackupManager.backup();

// A11yEnhancements.enableKeyboardNavigation();
// A11yEnhancements.announceToScreenReader('Attendance marked successfully');
