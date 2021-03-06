# This file is part of Scan.

# Scan is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Scan is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Scan.  If not, see <https://www.gnu.org/licenses/>.

import json
import os
import sys
from pathlib import Path

runtimeValues = {}

APP_SRC_DIR = os.getenv("APP_SRC_DIR", os.path.join(os.path.dirname(__file__), ".."))
TOOLS_CONFIG_DIR = os.getenv(
    "TOOLS_CONFIG_DIR", os.path.join(os.path.dirname(__file__), "..")
)

# Depth of credscan
credscan_depth = "5"
credscan_config = os.path.join(TOOLS_CONFIG_DIR, "credscan-config.toml")
credscan_timeout = "2m"

# Php memory limit
php_memory_limit = "2G"
phpstan_level = "5"
phpstan_config = os.path.join(TOOLS_CONFIG_DIR, "phpstan.neon.dist")

# Kotlint detekt config
detekt_config = os.path.join(TOOLS_CONFIG_DIR, "detekt-config.yml")
detekt_jar = "/usr/local/bin/detekt-cli.jar"

DEPSCAN_CMD = "/usr/local/bin/depscan"
PMD_CMD = "/opt/pmd-bin/bin/run.sh pmd"
SPOTBUGS_HOME = "/opt/spotbugs"

# Flag to disable telemetry
DISABLE_TELEMETRY = False

# Telemetry server
TELEMETRY_URL = "https://telemetry.appthreat.io/track"

# Line number hash size
HASH_DIGEST_SIZE = 8

# ShiftLeft NG SAST CLI command
SHIFTLEFT_NGSAST_CMD = "/opt/sl-cli/sl-latest"

# ShiftLeft URI
SHIFTLEFT_URI = "https://www.shiftleft.io"

# ShiftLeft vulnerabilities api url
SHIFTLEFT_VULN_API = "{}/api/v3/public/org/%(sl_org)s/app/%(app_name)s/version/%(version)s/vulnerabilities".format(
    SHIFTLEFT_URI
)

"""
Supported language scan types. Unused as a variable
"""
scan_types = [
    "ansible",
    "apex",
    "aws",
    "bash",
    "bom",
    "credscan",
    "depscan",
    "go",
    "groovy",
    "java",
    "jsp",
    "kotlin",
    "kubernetes",
    "nodejs",
    "plsql",
    "puppet",
    "php",
    "python",
    "ruby",
    "rust",
    "terraform",
    "vf",
    "vm",
    "yaml",
]


# Default ignore list
ignore_directories = [
    ".git",
    ".svn",
    ".mvn",
    ".idea",
    "dist",
    "obj",
    "backup",
    "docs",
    "tests",
    "test",
    "tmp",
    "report",
    "reports",
    "node_modules",
    ".terraform",
    ".serverless",
    "venv",
    ".virtualenv",
    "vendor",
    "bower_components",
    ".vscode",
]

# Ignore files list
ignore_files = [
    ".pyc",
    ".gz",
    ".tar",
    ".tar.gz",
    ".tar",
    ".md",
    ".log",
    ".tmp",
    ".bin",
    ".exe",
    ".dll",
    ".gif",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".d.ts",
    ".min.js",
    ".min.css",
    ".eslintrc.js",
    ".babelrc.js",
]


def get(configName, default_value=None):
    """Method to retrieve a config given a name. This method lazy loads configuration
    values and helps with overriding using a local config

    :param configName: Name of the config
    :return Config value
    """
    try:
        value = runtimeValues.get(configName)
        if value is None:
            value = os.environ.get(configName.upper())
        if value is None:
            value = getattr(sys.modules[__name__], configName, None)
        if value is None:
            value = default_value
        return value
    except Exception:
        return default_value


def set(configName, value):
    """Method to set a config during runtime

    :param configName: Config name
    :param value: Value
    """
    runtimeValues[configName] = value


"""
Mapping for application types to scan tools for projects requiring just a single tool
"""
scan_tools_args_map = {
    "ansible": [
        "ansible-lint",
        *["--exclude " + d for d in ignore_directories],
        "--parseable-severity",
        "*.yml",
    ],
    "apex": {
        "source-apex": [
            *get("PMD_CMD").split(" "),
            "-no-cache",
            "--failOnViolation",
            "false",
            "-language",
            "apex",
            "-d",
            "%(src)s",
            "-r",
            "%(report_fname_prefix)s.csv",
            "-f",
            "csv",
            "-R",
            get("TOOLS_CONFIG_DIR") + "/rules-pmd.xml",
        ]
    },
    "aws": {"source-aws": ["checkov", "-s", "--quiet", "-o", "json", "-d", "%(src)s"]},
    "bom": ["cdxgen", "-r", "-o", "%(report_fname_prefix)s.xml", "%(src)s"],
    "credscan": [
        "gitleaks",
        "--config=" + get("credscan_config"),
        "--depth=" + get("credscan_depth"),
        "--repo-path=%(src)s",
        "--redact",
        "--timeout=" + get("credscan_timeout"),
        "--report=%(report_fname_prefix)s.json",
        "--report-format=json",
    ],
    "credscan-raw": [
        "gitleaks",
        "--config=" + get("credscan_config"),
        "--depth=" + get("credscan_depth"),
        "--repo-path=%(src)s",
        "--report=%(report_fname_prefix)s.json",
        "--report-format=json",
    ],
    "credscan-ide": [
        "gitleaks",
        "--config=" + get("credscan_config"),
        "--uncommitted",
        "--repo-path=%(src)s",
        "--timeout=" + get("credscan_timeout"),
        "--report=%(report_fname_prefix)s.json",
        "--report-format=json",
    ],
    "bash": [
        "shellcheck",
        "-a",
        "--shell=%(type)s",
        "-f",
        "json",
        "-S",
        "error",
        "--color=never",
        "(filelist=sh)",
    ],
    "depscan": [
        get("DEPSCAN_CMD"),
        "--no-banner",
        "--src",
        "%(src)s",
        "--report_file",
        "%(report_fname_prefix)s.json",
    ],
    "go": {
        "source-go": [
            "gosec",
            "-fmt=json",
            "-confidence=medium",
            "-severity=medium",
            "-no-fail",
            "-out=%(report_fname_prefix)s.json",
            "./...",
        ],
        "staticcheck": ["staticcheck", "-f", "json", "./..."],
    },
    "jsp": {
        "source-jsp": [
            *get("PMD_CMD").split(" "),
            "-no-cache",
            "--failOnViolation",
            "false",
            "-language",
            "jsp",
            "-d",
            "%(src)s",
            "-r",
            "%(report_fname_prefix)s.csv",
            "-f",
            "csv",
            "-R",
            get("TOOLS_CONFIG_DIR") + "/rules-pmd.xml",
        ],
        "audit-jsp": [
            "java",
            "-jar",
            get("SPOTBUGS_HOME") + "/lib/spotbugs.jar",
            "-textui",
            "-include",
            get("TOOLS_CONFIG_DIR") + "/spotbugs/include.xml",
            "-exclude",
            get("TOOLS_CONFIG_DIR") + "/spotbugs/exclude.xml",
            "-noClassOk",
            "-sourcepath",
            "%(src)s",
            "-quiet",
            "-medium",
            "-xml:withMessages",
            "-effort:max",
            "-nested:false",
            "-output",
            "%(report_fname_prefix)s.xml",
            "%(src)s",
        ],
    },
    "kotlin": {
        "source-kt": [
            "java",
            "-jar",
            get("detekt_jar"),
            "-c",
            get("detekt_config"),
            "-i",
            "%(src)s",
            "-r",
            "xml:%(report_fname_prefix)s.xml",
        ],
        "audit-kt": [
            "java",
            "-jar",
            get("SPOTBUGS_HOME") + "/lib/spotbugs.jar",
            "-textui",
            "-include",
            get("TOOLS_CONFIG_DIR") + "/spotbugs/include.xml",
            "-exclude",
            get("TOOLS_CONFIG_DIR") + "/spotbugs/exclude.xml",
            "-noClassOk",
            "-sourcepath",
            "%(src)s",
            "-quiet",
            "-medium",
            "-xml:withMessages",
            "-effort:max",
            "-nested:false",
            "-output",
            "%(report_fname_prefix)s.xml",
            "%(src)s",
        ],
    },
    "kubernetes": {
        "source-k8s": ["checkov", "-s", "--quiet", "-o", "json", "-d", "%(src)s"],
        "kubesec": ["kubesec", "scan", "(filelist=yaml)"],
        "kube-score": [
            "kube-score",
            "score",
            "--output-version",
            "v2",
            "-o",
            "json",
            "(filelist=yaml)",
        ],
    },
    "plsql": {
        "source-sql": [
            *get("PMD_CMD").split(" "),
            "-no-cache",
            "--failOnViolation",
            "false",
            "-language",
            "plsql",
            "-d",
            "%(src)s",
            "-r",
            "%(report_fname_prefix)s.csv",
            "-f",
            "csv",
            "-R",
            get("TOOLS_CONFIG_DIR") + "/rules-pmd.xml",
        ]
    },
    "php-ide": {
        "source-php": [
            "phpstan",
            "analyse",
            "-c",
            get("phpstan_config"),
            "-l",
            get("phpstan_level"),
            "--no-progress",
            "--memory-limit",
            get("php_memory_limit"),
            "--error-format=json",
            "%(src)s",
        ],
        "audit-init": ["psalm", "--init", "--root=%(src)s", ".", "1"],
        "audit-php": [
            "psalm",
            "--report-show-info=false",
            "--show-snippet=true",
            "--find-dead-code=always",
            "--find-unused-code=always",
            "-m",
            "--no-progress",
            "--no-file-cache",
            "--no-suggestions",
            "--no-cache",
            "--root=%(src)s",
            "--report=" + "%(report_fname_prefix)s.json",
        ],
        "taint-php": [
            "/opt/phpsast/vendor/bin/psalm",
            "--report-show-info=false",
            "--show-snippet=true",
            "--taint-analysis",
            "-m",
            "--no-progress",
            "--no-file-cache",
            "--no-suggestions",
            "--no-cache",
            "--root=%(src)s",
            "--report=" + "%(report_fname_prefix)s.json",
        ],
    },
    "php": {
        "audit-init": ["psalm", "--init", "--root=%(src)s", ".", "1"],
        "audit-php": [
            "psalm",
            "--report-show-info=false",
            "--show-snippet=true",
            "--find-dead-code=always",
            "--find-unused-code=always",
            "-m",
            "--no-progress",
            "--no-file-cache",
            "--no-suggestions",
            "--no-cache",
            "--root=%(src)s",
            "--report=" + "%(report_fname_prefix)s.json",
        ],
        "taint-php": [
            "/opt/phpsast/vendor/bin/psalm",
            "--report-show-info=false",
            "--show-snippet=true",
            "--taint-analysis",
            "-m",
            "--no-progress",
            "--no-file-cache",
            "--no-suggestions",
            "--no-cache",
            "--root=%(src)s",
            "--report=" + "%(report_fname_prefix)s.json",
        ],
    },
    "puppet": ["puppet-lint", "--error-level", "all", "--json", "%(src)s"],
    "scala": {
        "audit-scala": [
            "java",
            "-jar",
            get("SPOTBUGS_HOME") + "/lib/spotbugs.jar",
            "-textui",
            "-include",
            get("TOOLS_CONFIG_DIR") + "/spotbugs/include.xml",
            "-exclude",
            get("TOOLS_CONFIG_DIR") + "/spotbugs/exclude.xml",
            "-noClassOk",
            "-sourcepath",
            "%(src)s",
            "-quiet",
            "-medium",
            "-xml:withMessages",
            "-effort:max",
            "-nested:false",
            "-output",
            "%(report_fname_prefix)s.xml",
            "%(src)s",
        ],
    },
    "groovy": {
        "audit-groovy": [
            "java",
            "-jar",
            get("SPOTBUGS_HOME") + "/lib/spotbugs.jar",
            "-textui",
            "-include",
            get("TOOLS_CONFIG_DIR") + "/spotbugs/include.xml",
            "-exclude",
            get("TOOLS_CONFIG_DIR") + "/spotbugs/exclude.xml",
            "-noClassOk",
            "-sourcepath",
            "%(src)s",
            "-quiet",
            "-medium",
            "-xml:withMessages",
            "-effort:max",
            "-nested:false",
            "-output",
            "%(report_fname_prefix)s.xml",
            "%(src)s",
        ],
    },
    "terraform": {
        "source-tf": ["checkov", "-s", "--quiet", "-o", "json", "-d", "%(src)s"],
        "tfsec": ["tfsec", "--format", "json", "--no-colour", "%(src)s"],
    },
    "vf": {
        "source-vf": [
            *get("PMD_CMD").split(" "),
            "-no-cache",
            "--failOnViolation",
            "false",
            "-language",
            "vf",
            "-d",
            "%(src)s",
            "-r",
            "%(report_fname_prefix)s.csv",
            "-f",
            "csv",
            "-R",
            get("TOOLS_CONFIG_DIR") + "/rules-pmd.xml",
        ]
    },
    "vm": {
        "source-vm": [
            *get("PMD_CMD").split(" "),
            "-no-cache",
            "--failOnViolation",
            "false",
            "-language",
            "vm",
            "-d",
            "%(src)s",
            "-r",
            "%(report_fname_prefix)s.csv",
            "-f",
            "csv",
            "-R",
            get("TOOLS_CONFIG_DIR") + "/rules-pmd.xml",
        ]
    },
    "yaml": {
        "yamllint": ["yamllint", "-f", "parsable", "(filelist=yaml)"],
        "source-yaml": ["checkov", "-s", "--quiet", "-o", "json", "-d", "%(src)s"],
    },
}

"""
Map of build tools for various language types. Used for auto build feature
"""
build_tools_map = {
    "csharp": ["dotnet", "build"],
    "java": {
        "maven": [get("MVN_CMD"), "compile"],
        "gradle": [get("GRADLE_CMD"), "compileJava"],
        "sbt": ["sbt", "compile"],
    },
    "android": {"gradle": [get("GRADLE_CMD"), "compileDebugSources"],},
    "kotlin": {
        "maven": [get("MVN_CMD"), "compile"],
        "gradle": [get("GRADLE_CMD"), "build"],
    },
    "groovy": {
        "maven": [get("MVN_CMD"), "compile"],
        "gradle": [get("GRADLE_CMD"), "compileGroovy"],
    },
    "scala": {
        "maven": [get("MVN_CMD"), "compile"],
        "gradle": [get("GRADLE_CMD"), "compileScala"],
        "sbt": ["sbt", "compile"],
    },
    "nodejs": {
        "npm": ["npm", "install"],
        "yarn": ["yarn", "install"],
        "rush": ["rush", "install", "--bypass-policy", "--no-link"],
    },
    "go": ["go", "build", "./..."],
    "php": {
        "init": ["composer", "init", "--quiet"],
        "install": ["composer", "install", "-n", "--ignore-platform-reqs"],
        "update": ["composer", "update", "-n", "--ignore-platform-reqs"],
    },
}

"""
This map contains the SARIF purpose string for various tools
"""
tool_purpose_message = {
    "nodejsscan": "Static security code scan",
    "njsscan": "Static security code scan",
    "findsecbugs": "Class file analyzer",
    "pmd": "Source code analyzer",
    "/opt/pmd-bin/bin/run.sh": "Source code analyzer",
    "gitleaks": "Secrets audit",
    "gosec": "Security audit for Go",
    "tfsec": "Terraform static analysis",
    "shellcheck": "Shell script analysis",
    "bandit": "Security audit for Python",
    "checkov": "Security audit for Infrastructure",
    "source-aws": "Security audit for AWS",
    "source-k8s": "Security audit for Kubernetes",
    "source-kt": "Static code analysis for Kotlin",
    "audit-kt": "Security audit for Kotlin",
    "audit-groovy": "Security audit for Groovy",
    "audit-scala": "Security audit for Scala",
    "detekt": "Static code analysis for Kotlin",
    "source-tf": "Security audit for Terraform",
    "source-yaml": "Security audit for IaC",
    "staticcheck": "Go static analysis",
    "source": "Source code analyzer",
    "source-java": "Source code analyzer for Java",
    "source-python": "Source code analyzer for Python",
    "source-php": "Source code analyzer for PHP",
    "phpstan": "Source code analyzer for PHP",
    "audit-php": "Security audit for PHP",
    "taint-php": "Security taint analysis for PHP",
    "psalm": "Security audit for PHP",
    "/opt/phpsast/vendor/bin/psalm": "Security taint analysis for PHP",
    "source-js": "Source code analyzer for JavaScript",
    "source-go": "Source code analyzer for Go",
    "source-vm": "Source code analyzer for Apache Velocity",
    "source-vf": "Source code analyzer for VisualForce",
    "source-sql": "Source code analyzer for SQL",
    "source-jsp": "Source code analyzer for JSP",
    "audit-jsp": "Security audit for JSP",
    "source-apex": "Source code analyzer for apex",
    "binary": "Binary byte-code analyzer",
    "class": "Class file analyzer",
    "jar": "Jar file analyzer",
    "cpg": "ShiftLeft graph analyzer",
    "inspect": "ShiftLeft NG SAST analyzer",
    "ng-sast": "ShiftLeft NG SAST analyzer",
}

# Map to link to the reference for the given rule
tool_ref_url = {
    "shellcheck": "https://github.com/koalaman/shellcheck/wiki/SC%(rule_id)s",
    "staticcheck": "https://staticcheck.io/docs/checks#%(rule_id)s",
}

# Rules to ignore
ignored_rules = [
    "GEN001",
    "GEN002",
    "GEN003",
    "AWS002",
    "AWS018",
    "AWS019",
    "Password Hardcoded",
    "Secret Hardcoded",
    "DuplicateArrayKey",
    "DeprecatedFunction",
    "DeprecatedInterface",
    "DeprecatedConstant",
    "DeprecatedMethod",
    "FalsableReturnStatement",
    "ImplicitToStringCast",
    "InternalClass",
    "InternalMethod",
    "InternalProperty",
    "InvalidArgument",
    "InvalidArrayAccess",
    "InvalidArrayAssignment",
    "InvalidArrayOffset",
    "InvalidCast",
    "InvalidCatch",
    "InvalidClass",
    "InvalidExtendClass",
    "InvalidClone",
    "InvalidDocblock",
    "InvalidDocblockParamName",
    "InvalidFalsableReturnType",
    "InvalidFunctionCall",
    "InvalidGlobal",
    "InvalidIterator",
    "InvalidMethodCall",
    "InvalidNullableReturnType",
    "InvalidOperand",
    "InvalidParamDefault",
    "InvalidParent",
    "InvalidPassByReference",
    "InvalidPropertyAssignment",
    "InvalidPropertyAssignmentValue",
    "InvalidPropertyFetch",
    "InvalidReturnStatement",
    "InvalidReturnType",
    "InvalidScalarArgument",
    "InvalidScope",
    "InvalidStaticInvocation",
    "InvalidStringClass",
    "InvalidTemplateParam",
    "InvalidThrow",
    "InvalidToString",
    "MissingClosureParamType",
    "MissingClosureReturnType",
    "MissingConstructor",
    "MissingDependency",
    "MissingDocblockType",
    "MissingFile",
    "MissingImmutableAnnotation",
    "MissingParamType",
    "MissingPropertyType",
    "MissingReturnType",
    "MissingTemplateParam",
    "MissingThrowsDocblock",
    "MismatchingDocblockParamType",
    "MismatchingDocblockReturnType",
    "MixedArgument",
    "MixedArgumentTypeCoercion",
    "MixedArrayAccess",
    "MixedArrayAssignment",
    "MixedArrayOffset",
    "MixedArrayTypeCoercion",
    "MixedAssignment",
    "MixedClone",
    "MixedFunctionCall",
    "MixedInferredReturnType",
    "MixedMethodCall",
    "MixedOperand",
    "MixedPropertyAssignment",
    "MixedPropertyFetch",
    "MixedPropertyTypeCoercion",
    "MixedReturnStatement",
    "MixedReturnTypeCoercion",
    "MixedStringOffsetAssignment",
    "NullableReturnStatement",
    "PossibleRawObjectIteration",
    "PossiblyFalseArgument",
    "PossiblyFalseIterator",
    "PossiblyFalseOperand",
    "PossiblyFalsePropertyAssignmentValue",
    "PossiblyFalseReference",
    "PossiblyInvalidArgument",
    "PossiblyInvalidArrayAccess",
    "PossiblyInvalidArrayAssignment",
    "PossiblyInvalidArrayOffset",
    "PossiblyInvalidCast",
    "PossiblyInvalidFunctionCall",
    "PossiblyInvalidIterator",
    "PossiblyInvalidMethodCall",
    "PossiblyInvalidOperand",
    "PossiblyInvalidPropertyAssignment",
    "PossiblyInvalidPropertyAssignmentValue",
    "PossiblyInvalidPropertyFetch",
    "PossiblyNullArgument",
    "PossiblyNullArrayAccess",
    "PossiblyNullArrayAssignment",
    "PossiblyNullArrayOffset",
    "PossiblyNullFunctionCall",
    "PossiblyNullIterator",
    "PossiblyNullOperand",
    "PossiblyNullPropertyAssignment",
    "PossiblyNullPropertyAssignmentValue",
    "PossiblyNullPropertyFetch",
    "PossiblyNullReference",
    "PossiblyUndefinedArrayOffset",
    "PossiblyUndefinedGlobalVariable",
    "PossiblyUndefinedIntArrayOffset",
    "PossiblyUndefinedMethod",
    "PossiblyUndefinedStringArrayOffset",
    "PossiblyUndefinedVariable",
    "PossiblyUnusedMethod",
    "PossiblyUnusedParam",
    "PossiblyUnusedProperty",
    "PropertyNotSetInConstructor",
    "RedundantCondition",
    "RedundantConditionGivenDocblockType",
    "LessSpecificImplementedReturnType",
    "LessSpecificReturnStatement",
    "LessSpecificReturnType",
    "DocblockTypeContradiction",
    "UndefinedClass",
    "UndefinedConstant",
    "UndefinedDocblockClass",
    "UndefinedFunction",
    "UndefinedGlobalVariable",
    "UndefinedInterface",
    "UndefinedInterfaceMethod",
    "UndefinedMagicMethod",
    "UndefinedMagicPropertyAssignment",
    "UndefinedMagicPropertyFetch",
    "UndefinedMethod",
    "UndefinedPropertyAssignment",
    "UndefinedPropertyFetch",
    "UndefinedThisPropertyAssignment",
    "UndefinedThisPropertyFetch",
    "UndefinedTrait",
    "UndefinedVariable",
    "UnevaluatedCode",
    "UnimplementedAbstractMethod",
    "UnimplementedInterfaceMethod",
    "UninitializedProperty",
    "UnnecessaryVarAnnotation",
    "UnrecognizedExpression",
    "UnrecognizedStatement",
    "UnresolvableInclude",
    "UnusedClass",
    "UnusedClosureParam",
    "UnusedFunctionCall",
    "UnusedMethod",
    "UnusedMethodCall",
    "UnusedParam",
    "UnusedProperty",
    "UnusedPsalmSuppress",
    "UnusedVariable",
    "phpstan-phpdoc",
    "phpstan-constant",
    "phpstan-if",
    "phpstan-property",
    "phpstan-variable",
    "phpstan-negated",
    "phpstan-cannot",
    "phpstan-result",
]

# Override severity of certain rules
rules_severity = {
    "RCE": "CRITICAL",
    "RCI": "HIGH",
    "SSRF": "CRITICAL",
    "MODULE": "MEDIUM",
    "DIR": "HIGH",
    "SQLI": "CRITICAL",
    "XSS": "MEDIUM",
    "NOSQLI": "HIGH",
    "HHI": "MEDIUM",
    "NODE": "MEDIUM",
    "CKV_AWS_2": "HIGH",
    "CKV_AWS_23": "LOW",
    "CKV_AWS_33": "LOW",
    "CKV_AWS_40": "MEDIUM",
    "CKV_AWS_50": "MEDIUM",
    "CKV_AWS_51": "LOW",
    "AWS007": "HIGH",
    "AWS008": "MEDIUM",
    "AWS009": "HIGH",
    "AWS011": "HIGH",
    "AWS017": "HIGH",
    "CKV_AWS_28": "MEDIUM",
    "CKV_AWS_32": "CRITICAL",
    "CKV_AWS_34": "MEDIUM",
    "CKV_AWS_38": "HIGH",
    "CKV_K8S_14": "MEDIUM",
    "CKV_K8S_21": "CRITICAL",
    "CKV_K8S_27": "CRITICAL",
    "CKV_K8S_29": "MEDIUM",
    "CKV_K8S_34": "CRITICAL",
    "CKV_K8S_4": "CRITICAL",
    "CKV_K8S_5": "CRITICAL",
    "CKV_K8S_6": "CRITICAL",
    "CKV_AWS_46": "CRITICAL",
}

# Build break rules
build_break_rules = {"default": {"max_critical": 0, "max_high": 2, "max_medium": 5}}

# URL for viewing reports online
hosted_viewer_uri = "https://sarifviewer.azurewebsites.net"


def reload():
    # Load any .sastscanrc file from the root
    if get("SAST_SCAN_SRC_DIR"):
        scanrc = os.path.join(get("SAST_SCAN_SRC_DIR"), ".sastscanrc")
        if os.path.exists(scanrc):
            with open(scanrc, "r") as rcfile:
                new_config = json.loads(rcfile.read())
                for key, value in new_config.items():
                    exis_config = get(key)
                    if isinstance(exis_config, dict):
                        exis_config = exis_config.update(value)
                        set(key, exis_config)
                    else:
                        set(key, value)
