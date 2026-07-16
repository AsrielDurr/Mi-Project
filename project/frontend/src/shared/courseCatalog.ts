export interface CourseOption {
  courseId: string;
  name: string;
}


export const courseCatalog: readonly CourseOption[] = [
  { courseId: "CS101", name: "Python程序设计" },
  { courseId: "AI201", name: "人工智能基础" },
  { courseId: "DB202", name: "数据库系统" },
  { courseId: "ML301", name: "机器学习" },
  { courseId: "CV401", name: "计算机视觉" },
  { courseId: "WEB201", name: "Web开发" },
  { courseId: "ALG201", name: "数据结构" },
  { courseId: "NET301", name: "计算机网络" },
];

