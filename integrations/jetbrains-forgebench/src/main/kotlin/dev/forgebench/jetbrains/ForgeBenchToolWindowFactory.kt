package dev.forgebench.jetbrains

import com.intellij.openapi.project.Project
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowFactory
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.content.ContentFactory
import java.awt.BorderLayout
import javax.swing.JButton
import javax.swing.JPanel
import javax.swing.JTextArea

class ForgeBenchToolWindowFactory : ToolWindowFactory {
    override fun createToolWindowContent(project: Project, toolWindow: ToolWindow) {
        val panel = JPanel(BorderLayout())
        val output = JTextArea("ForgeBench — use the buttons below or Tools → ForgeBench.\n")
        output.isEditable = false
        panel.add(JBScrollPane(output), BorderLayout.CENTER)

        val actions = JPanel()
        val reviewBtn = JButton("Review diff")
        reviewBtn.addActionListener {
            output.text = "Use Tools → ForgeBench → Review Diff + Task to pick diff and task files.\n"
        }
        val demoBtn = JButton("Run demo")
        demoBtn.addActionListener {
            val result = ForgeBenchCli.run(project, listOf("demo", "--repo", project.basePath ?: "."))
            output.text = result.output
        }
        val statusBtn = JButton("Status")
        statusBtn.addActionListener {
            val result = ForgeBenchCli.run(project, listOf("status", "--repo", project.basePath ?: "."))
            output.text = result.output
        }
        val repairBtn = JButton("Repair prompt")
        repairBtn.addActionListener {
            val repair = java.io.File(ForgeBenchCli.outputDir(project), "repair-prompt.md")
            output.text = if (repair.exists()) {
                repair.readText()
            } else {
                "No repair prompt found. Run a review first.\n"
            }
        }
        actions.add(reviewBtn)
        actions.add(demoBtn)
        actions.add(statusBtn)
        actions.add(repairBtn)
        panel.add(actions, BorderLayout.NORTH)

        val content = ContentFactory.getInstance().createContent(panel, "", false)
        toolWindow.contentManager.addContent(content)
    }
}