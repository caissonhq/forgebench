package dev.forgebench.jetbrains

import com.intellij.openapi.project.Project
import java.io.File
import java.nio.charset.StandardCharsets
import java.util.concurrent.TimeUnit

object ForgeBenchCli {
    fun run(project: Project, args: List<String>, timeoutSeconds: Long = 120): ForgeBenchCliResult {
        val workDir = project.basePath?.let { File(it) } ?: File(".")
        val command = mutableListOf(System.getenv("FORGEBENCH_BIN") ?: "forgebench")
        command.addAll(args)
        val process = ProcessBuilder(command)
            .directory(workDir)
            .redirectErrorStream(true)
            .start()
        val finished = process.waitFor(timeoutSeconds, TimeUnit.SECONDS)
        val output = process.inputStream.bufferedReader(StandardCharsets.UTF_8).readText()
        if (!finished) {
            process.destroyForcibly()
            return ForgeBenchCliResult(exitCode = 124, output = output + "\nTimed out after ${timeoutSeconds}s")
        }
        return ForgeBenchCliResult(exitCode = process.exitValue(), output = output)
    }

    fun outputDir(project: Project): File {
        val base = project.basePath?.let { File(it) } ?: File(".")
        return File(base, "forgebench-output")
    }
}

data class ForgeBenchCliResult(
    val exitCode: Int,
    val output: String,
)